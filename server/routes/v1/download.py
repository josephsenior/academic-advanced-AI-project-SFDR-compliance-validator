from __future__ import annotations

import logging
import os
from pathlib import Path

from flask import current_app, jsonify, request, send_file

from ...store import validation_jobs

from . import bp

logger = logging.getLogger(__name__)


@bp.get("/download/<document_id>")
def download_document(document_id: str):
    try:
        if document_id not in validation_jobs:
            logger.info("Download requested for missing document_id=%s", document_id)
            return jsonify({"error": "Document not found"}), 404

        job = validation_jobs[document_id]
        download_type = request.args.get("type", "corrected")

        # Normalize and check file paths for both original and corrected
        if download_type == "original":
            original_path = job.get("file_path") or ""
            # Ensure path is absolute
            if original_path and not os.path.isabs(original_path):
                project_root = Path(current_app.root_path).parent
                original_path = str(project_root / original_path)
            file_path = Path(original_path)
            if not file_path.exists():
                logger.info("Original file missing for document_id=%s path=%s", document_id, str(file_path))
                return jsonify({"error": "Original document not found"}), 404
        else:
            file_path = Path(current_app.config.get("CORRECTED_FOLDER", "corrected_documents")) / f"{document_id}_corrected.pptx"
            
            # EMERGENCY DEBUG LOG
            DEBUG_FILE = r"C:\Users\GIGABYTE\Desktop\Advanced Ai Project\debug_fix_abs.log"
            try:
                import os
                from datetime import datetime
                with open(DEBUG_FILE, "a") as f:
                    f.write(f"\n--- DOWNLOAD {datetime.now()} ---\n")
                    f.write(f"Checking: {file_path}\n")
                    f.write(f"Exists: {file_path.exists()}\n")
            except:
                pass
                
            if not file_path.exists():
                logger.info("Corrected file missing for document_id=%s path=%s", document_id, str(file_path))
                return jsonify({"error": "Corrected document not found. Run /api/v1/fix first"}), 404

        # Ensure we pass a string path to send_file and log the action
        file_path_str = str(file_path.resolve())
        logger.info("Serving file for document_id=%s path=%s", document_id, file_path_str)
        return send_file(file_path_str, as_attachment=True, download_name=f"{download_type}_{job.get('filename', document_id)}")

    except Exception:
        logger.exception("Download error for %s", document_id)
        return jsonify({"error": "Download failed due to server error"}), 500
