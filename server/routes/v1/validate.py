from __future__ import annotations

import logging
from typing import Any, Dict

from flask import jsonify, request

from ...constants import ValidationStatus
from ...store import update_job_status, validation_jobs

from . import bp

logger = logging.getLogger(__name__)


@bp.post("/validate/<document_id>")
def validate_document(document_id: str):
    try:
        if document_id not in validation_jobs:
            return jsonify({"error": "Document not found"}), 404

        job = validation_jobs[document_id]

        if job["status"] in [ValidationStatus.EXTRACTING, ValidationStatus.VALIDATING]:
            return jsonify(
                {
                    "document_id": document_id,
                    "status": job["status"],
                    "progress": job["progress"],
                    "message": "Validation already in progress",
                }
            )

        options: Dict[str, Any] = {}
        if request.is_json:
            data = request.get_json() or {}
            options = data.get("options", {})
            if "metadata" in data:
                job["metadata"] = {**job["metadata"], **data["metadata"]} if job.get("metadata") else data["metadata"]

        # Lazy import: pulls in pipeline/LLM deps only when validation runs.
        from ...services.validation_service import run_validation

        formatted_result = run_validation(document_id, job, options)

        return jsonify(
            {
                "document_id": document_id,
                "status": ValidationStatus.COMPLETED,
                "progress": 100,
                "message": "Validation completed",
                "results": formatted_result,
            }
        )

    except Exception as e:
        logger.error("Validation error for %s: %s", document_id, str(e), exc_info=True)
        update_job_status(document_id, ValidationStatus.FAILED, error=str(e))
        return jsonify({"error": f"Validation failed: {str(e)}"}), 500
