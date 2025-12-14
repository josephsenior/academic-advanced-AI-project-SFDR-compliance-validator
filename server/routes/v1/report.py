from __future__ import annotations

import json
import logging
from pathlib import Path

from flask import current_app, jsonify, send_file, request

from ...constants import ValidationStatus
from ...store import validation_jobs

from . import bp

logger = logging.getLogger(__name__)


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
                return send_file(
                    str(output_path),
                    mimetype="application/pdf",
                    as_attachment=True,
                    download_name=f"validation_report_{document_id}.pdf",
                )
            except Exception as e:
                logger.error("PDF generation failed for %s: %s", document_id, e, exc_info=True)
                return jsonify({"error": f"PDF generation failed: {str(e)}"}), 500

        return jsonify({"error": f"Unsupported format: {report_format}"}), 400

    except Exception as e:
        logger.error("Report generation error for %s: %s", document_id, str(e), exc_info=True)
        return jsonify({"error": f"Report generation failed: {str(e)}"}), 500
