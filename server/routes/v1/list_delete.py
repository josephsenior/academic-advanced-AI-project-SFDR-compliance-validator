from __future__ import annotations

import logging
from pathlib import Path

from flask import current_app, jsonify, request

from ...store import validation_jobs

from . import bp

logger = logging.getLogger(__name__)


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
