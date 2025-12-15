from __future__ import annotations

from datetime import datetime
from pathlib import Path

from flask import current_app, jsonify

from ...store import validation_jobs

from . import bp


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
