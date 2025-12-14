from __future__ import annotations

import logging
from pathlib import Path

from flask import current_app, jsonify, request

from ...constants import ValidationStatus
from ...store import validation_jobs

from . import bp

logger = logging.getLogger(__name__)


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

        # Lazy import to avoid heavy deps at startup
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

        return jsonify(
            {
                "document_id": document_id,
                "corrected_file_path": str(output_path),
                "fixes_applied": fixes_applied,
                "message": f"Document corrected successfully. {fixes_applied} fixes applied.",
            }
        )

    except Exception as e:
        logger.error("Fix error for %s: %s", document_id, str(e), exc_info=True)
        return jsonify({"error": f"Fix failed: {str(e)}"}), 500
