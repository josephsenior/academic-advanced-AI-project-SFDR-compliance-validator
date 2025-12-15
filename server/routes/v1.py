from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from flask import Blueprint, current_app, jsonify, request, send_file
from werkzeug.utils import secure_filename

from ..constants import ALLOWED_EXTENSIONS, ValidationStatus
from ..store import create_job_record, update_job_status, validation_jobs

logger = logging.getLogger(__name__)

bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.get("/health")
def health_check():
    return jsonify({"status": "healthy", "version": "1.0.0", "timestamp": datetime.utcnow().isoformat()})


@bp.post("/upload")
def upload_document():
    try:
        # Backward-compatible: older clients/tests use the field name `file`.
        document_file = request.files.get("document") or request.files.get("file")
        if document_file is None:
            return jsonify({"error": "No document file provided. Please upload the main document."}), 400
        if document_file.filename == "":
            return jsonify({"error": "No document file selected"}), 400

        if not allowed_file(document_file.filename):
            return jsonify({"error": f"Document file type not supported. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"}), 400

        document_id = str(uuid.uuid4())

        doc_dir = Path(current_app.config["UPLOAD_FOLDER"]) / document_id
        doc_dir.mkdir(parents=True, exist_ok=True)

        filename = secure_filename(document_file.filename)
        file_path = doc_dir / filename
        document_file.save(file_path)

        metadata = None
        has_metadata = False

        # Option A: metadata provided as uploaded JSON file.
        metadata_file = request.files.get("metadata")
        if metadata_file and metadata_file.filename and metadata_file.filename.endswith(".json"):
            try:
                metadata = json.load(metadata_file)
                metadata_path = doc_dir / "metadata.json"
                with open(metadata_path, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
                has_metadata = True
                logger.info("Metadata uploaded for %s", document_id)
            except Exception as e:
                logger.warning("Failed to parse metadata file: %s", e)

        # Option B (legacy): metadata provided as form field containing JSON.
        if not has_metadata:
            metadata_raw = request.form.get("metadata")
            if metadata_raw:
                try:
                    metadata = json.loads(metadata_raw)
                    metadata_path = doc_dir / "metadata.json"
                    with open(metadata_path, "w", encoding="utf-8") as f:
                        json.dump(metadata, f, indent=2, ensure_ascii=False)
                    has_metadata = True
                    logger.info("Metadata (form) uploaded for %s", document_id)
                except Exception as e:
                    logger.warning("Failed to parse metadata form field: %s", e)

        has_prospectus = False
        if "prospectus" in request.files:
            prospectus_file = request.files["prospectus"]
            if prospectus_file.filename:
                prospectus_filename = secure_filename(prospectus_file.filename)
                prospectus_path = doc_dir / f"prospectus_{prospectus_filename}"
                prospectus_file.save(prospectus_path)
                has_prospectus = True
                logger.info("Prospectus uploaded for %s: %s", document_id, prospectus_filename)

        job = create_job_record(document_id, filename, str(file_path))
        job["metadata"] = metadata
        job["has_prospectus"] = has_prospectus
        validation_jobs[document_id] = job

        logger.info("Upload complete: %s - %s (metadata: %s, prospectus: %s)", document_id, filename, has_metadata, has_prospectus)

        return (
            jsonify(
                {
                    "document_id": document_id,
                    "filename": filename,
                    "status": ValidationStatus.PENDING,
                    "message": "Upload successful. Use /api/v1/validate/{document_id} to start validation.",
                    "has_metadata": has_metadata,
                    "has_prospectus": has_prospectus,
                    "note": "Prospectus is optional. Without it, performance data validation will be limited.",
                }
            ),
            201,
        )

    except Exception as e:
        logger.error("Upload error: %s", str(e), exc_info=True)
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500


@bp.post("/validate/<document_id>")
def validate_document(document_id: str):
    try:
        if document_id not in validation_jobs:
            return jsonify({"error": "Document not found"}), 404

        job = validation_jobs[document_id]

        if job["status"] in [ValidationStatus.EXTRACTING, ValidationStatus.VALIDATING]:
            return jsonify({"document_id": document_id, "status": job["status"], "progress": job["progress"], "message": "Validation already in progress"})

        options: Dict[str, Any] = {}
        if request.is_json:
            data = request.get_json() or {}
            options = data.get("options", {})
            if "metadata" in data:
                job["metadata"] = {**job["metadata"], **data["metadata"]} if job.get("metadata") else data["metadata"]

        from ..services.validation_service import run_validation

        formatted_result = run_validation(document_id, job, options)

        return jsonify({"document_id": document_id, "status": ValidationStatus.COMPLETED, "progress": 100, "message": "Validation completed", "results": formatted_result})

    except Exception as e:
        logger.error("Validation error for %s: %s", document_id, str(e), exc_info=True)
        update_job_status(document_id, ValidationStatus.FAILED, error=str(e))
        return jsonify({"error": f"Validation failed: {str(e)}"}), 500


@bp.get("/status/<document_id>")
def get_status(document_id: str):
    if document_id not in validation_jobs:
        output_path = Path(current_app.config["OUTPUT_FOLDER"]) / document_id
        if not output_path.exists():
            return jsonify({"error": "Document not found"}), 404

        validation_file = output_path / "validation_result.json"
        if validation_file.exists():
            return jsonify(
                {
                    "document_id": document_id,
                    "filename": "Unknown",
                    "status": "completed",
                    "progress": 100,
                    "created_at": datetime.fromtimestamp(output_path.stat().st_ctime).isoformat(),
                    "updated_at": datetime.fromtimestamp(validation_file.stat().st_mtime).isoformat(),
                }
            )

        return jsonify({"error": "Document not found"}), 404

    job = validation_jobs[document_id]
    return jsonify(
        {
            "document_id": document_id,
            "filename": job["filename"],
            "status": job["status"],
            "progress": job["progress"],
            "created_at": job["created_at"],
            "updated_at": job["updated_at"],
            "error": job.get("error"),
        }
    )


@bp.get("/results/<document_id>")
def get_results(document_id: str):
    if document_id not in validation_jobs:
        output_path = Path(current_app.config["OUTPUT_FOLDER"]) / document_id / "validation_result.json"
        if not output_path.exists():
            return jsonify({"error": "Document not found"}), 404

        try:
            with open(output_path, "r", encoding="utf-8") as f:
                results = json.load(f)
            return jsonify(results), 200
        except Exception as e:
            logger.error("Failed to load results from disk: %s", e)
            return jsonify({"error": "Failed to load results"}), 500

    job = validation_jobs[document_id]

    if job["status"] != ValidationStatus.COMPLETED:
        return jsonify({"error": "Validation not completed", "status": job["status"], "progress": job["progress"]}), 400

    results = job["validation_result"]

    category_filter = request.args.get("category")
    severity_filter = request.args.get("severity")
    slide_filter = request.args.get("slide", type=int)

    if any([category_filter, severity_filter, slide_filter]):
        filtered_issues = {}
        for category, issues in results["issues_by_category"].items():
            if category_filter and category != category_filter:
                continue

            filtered = [
                issue
                for issue in issues
                if (not severity_filter or issue["severity"] == severity_filter)
                and (not slide_filter or issue.get("slide_number") == slide_filter)
            ]

            if filtered:
                filtered_issues[category] = filtered

        results = {**results, "issues_by_category": filtered_issues}

    return jsonify(results)


@bp.post("/fix/<document_id>")
def fix_document(document_id: str):
    try:
        if document_id not in validation_jobs:
            return jsonify({"error": "Document not found"}), 404

        job = validation_jobs[document_id]

        if job["status"] != ValidationStatus.COMPLETED:
            return jsonify({"error": "Validation must be completed first"}), 400

        data = request.get_json() or {}
        fix_types = data.get("fix_types", ["all"])

        from backend.extractors.document_corrector import DocumentCorrector

        corrector = DocumentCorrector()

        original_path = job["file_path"]
        output_path = Path(current_app.config["CORRECTED_FOLDER"]) / f"{document_id}_corrected.pptx"

        logger.info("Applying fixes to %s", document_id)

        validation_result = job["validation_result"]
        issues_to_fix = []

        for category, issues in validation_result["issues_by_category"].items():
            for issue in issues:
                if issue.get("auto_fixable", False) and ("all" in fix_types or category in fix_types):
                    issues_to_fix.append(issue)

        corrector.correct(original_path, job["validation_result"], output_path=str(output_path))

        fixes_applied = len(issues_to_fix)

        return jsonify({"document_id": document_id, "corrected_file_path": str(output_path), "fixes_applied": fixes_applied, "message": f"Document corrected successfully. {fixes_applied} fixes applied."})

    except Exception as e:
        logger.error("Fix error for %s: %s", document_id, str(e), exc_info=True)
        return jsonify({"error": f"Fix failed: {str(e)}"}), 500


@bp.get("/download/<document_id>")
def download_document(document_id: str):
    try:
        if document_id not in validation_jobs:
            return jsonify({"error": "Document not found"}), 404

        job = validation_jobs[document_id]
        download_type = request.args.get("type", "corrected")

        if download_type == "original":
            file_path = job["file_path"]
        else:
            file_path = Path(current_app.config["CORRECTED_FOLDER"]) / f"{document_id}_corrected.pptx"
            if not file_path.exists():
                return jsonify({"error": "Corrected document not found. Run /api/v1/fix first"}), 404

        return send_file(file_path, as_attachment=True, download_name=f"{download_type}_{job['filename']}")

    except Exception as e:
        logger.error("Download error for %s: %s", document_id, str(e), exc_info=True)
        return jsonify({"error": f"Download failed: {str(e)}"}), 500


@bp.get("/report/<document_id>")
def generate_report(document_id: str):
    try:
        validation_result = None
        filename = None

        if document_id in validation_jobs:
            job = validation_jobs[document_id]
            if job["status"] != ValidationStatus.COMPLETED:
                return jsonify({"error": "Validation not completed"}), 400
            validation_result = job["validation_result"]
            filename = job.get("filename")
        else:
            output_dir = Path(current_app.config["OUTPUT_FOLDER"]) / document_id
            validation_file = output_dir / "validation_result.json"
            if not validation_file.exists():
                return jsonify({"error": "Document not found"}), 404
            try:
                with open(validation_file, "r", encoding="utf-8") as f:
                    validation_result = json.load(f)
            except Exception as e:
                logger.error("Failed to load validation result for report: %s", e)
                return jsonify({"error": "Failed to load validation results"}), 500

        report_format = request.args.get("format", "json")

        if report_format == "json":
            return jsonify(validation_result)

        from backend.utils.reporting.validation_report_generator import ValidationReportGenerator

        generator = ValidationReportGenerator()
        output_dir = Path(current_app.config["OUTPUT_FOLDER"]) / document_id
        output_dir.mkdir(parents=True, exist_ok=True)

        if report_format == "html":
            output_path = output_dir / "report.html"
            generator.generate_html_report(validation_result, output_path)
            return send_file(str(output_path), mimetype="text/html")

        if report_format == "pdf":
            output_path = output_dir / "report.pdf"
            try:
                generator.generate_pdf_report(validation_result, output_path, filename)
                return send_file(str(output_path), mimetype="application/pdf", as_attachment=True, download_name=f"validation_report_{document_id}.pdf")
            except Exception as e:
                logger.error("PDF generation failed for %s: %s", document_id, e, exc_info=True)
                return jsonify({"error": f"PDF generation failed: {str(e)}"}), 500

        return jsonify({"error": f"Unsupported format: {report_format}"}), 400

    except Exception as e:
        logger.error("Report generation error for %s: %s", document_id, str(e), exc_info=True)
        return jsonify({"error": f"Report generation failed: {str(e)}"}), 500


@bp.get("/list")
def list_documents():
    status_filter = request.args.get("status")
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)

    filtered_jobs = []
    for job_id, job in validation_jobs.items():
        if status_filter and job["status"] != status_filter:
            continue

        filtered_jobs.append(
            {
                "document_id": job_id,
                "filename": job["filename"],
                "status": job["status"],
                "progress": job["progress"],
                "created_at": job["created_at"],
                "updated_at": job["updated_at"],
                "compliance_score": job["validation_result"].get("compliance_score") if job.get("validation_result") else None,
                "total_issues": job["validation_result"].get("total_issues") if job.get("validation_result") else None,
            }
        )

    filtered_jobs.sort(key=lambda x: x["created_at"], reverse=True)

    total = len(filtered_jobs)
    paginated = filtered_jobs[offset : offset + limit]

    return jsonify({"total": total, "limit": limit, "offset": offset, "documents": paginated})


@bp.delete("/delete/<document_id>")
def delete_document(document_id: str):
    try:
        if document_id not in validation_jobs:
            return jsonify({"error": "Document not found"}), 404

        job = validation_jobs[document_id]

        try:
            Path(job["file_path"]).unlink(missing_ok=True)
        except Exception:
            pass

        try:
            output_dir = Path(current_app.config["OUTPUT_FOLDER"]) / document_id
            if output_dir.exists():
                import shutil

                shutil.rmtree(output_dir)
        except Exception:
            pass

        try:
            corrected_path = Path(current_app.config["CORRECTED_FOLDER"]) / f"{document_id}_corrected.pptx"
            corrected_path.unlink(missing_ok=True)
        except Exception:
            pass

        del validation_jobs[document_id]

        logger.info("Deleted document %s", document_id)
        return jsonify({"message": "Document deleted successfully", "document_id": document_id})

    except Exception as e:
        logger.error("Delete error for %s: %s", document_id, str(e), exc_info=True)
        return jsonify({"error": f"Delete failed: {str(e)}"}), 500
