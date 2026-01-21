from __future__ import annotations

import logging
import os
from pathlib import Path

from flask import current_app, jsonify, request, send_file

from ... import store
from ...store import validation_jobs

from . import bp

logger = logging.getLogger(__name__)


@bp.get("/download/<document_id>")
def download_document(document_id: str):
    """Serve original or corrected documents."""
    try:
        logger.info("Download requested for document_id=[%s]", document_id)
        if document_id not in validation_jobs:
            logger.info("Document ID [%s] not found in job store. Available IDs: %s", document_id, list(validation_jobs.keys()))
            return jsonify({"error": f"Document ID {document_id} not found in job store"}), 404

        job = validation_jobs[document_id]
        download_type = request.args.get("type", "corrected")
        
        # Get project root
        project_root = Path(current_app.root_path).parent

        if download_type == "original":
            original_path_str = job.get("file_path") or ""
            if not original_path_str:
                return jsonify({"error": "Original file path missing in job record"}), 404
            
            file_path = Path(original_path_str)
            if not file_path.is_absolute():
                file_path = project_root / file_path
                
            if not file_path.exists():
                logger.info("Original file missing for document_id=%s path=%s", document_id, str(file_path))
                return jsonify({"error": f"Original document file not found at {file_path}"}), 404
        else:
            # Look in CORRECTED_FOLDER
            corrected_folder = current_app.config.get("CORRECTED_FOLDER")
            if not corrected_folder:
                 corrected_folder = str(project_root / "corrected_documents")
            
            file_path = Path(corrected_folder) / f"{document_id}_corrected.pptx"
            
            if not file_path.exists():
                # Try fallback: maybe it's in outputs folder?
                output_folder = current_app.config.get("OUTPUT_FOLDER") or str(project_root / "outputs")
                fallback_path = Path(output_folder) / f"corrected_{document_id}.pptx"
                if fallback_path.exists():
                    file_path = fallback_path
                else:
                    logger.info("Corrected file missing for document_id=%s path=%s", document_id, str(file_path))
                    return jsonify({"error": "Corrected document not found. Run /api/v1/fix first"}), 404

        # Ensure we pass an absolute string path to send_file
        abs_file_path = str(file_path.absolute())
        logger.info("Serving file for document_id=%s type=%s path=%s", document_id, download_type, abs_file_path)
        
        if not os.path.exists(abs_file_path):
             return jsonify({"error": f"Resolved path does not exist: {abs_file_path}"}), 404

        return send_file(
            abs_file_path, 
            as_attachment=True, 
            download_name=f"{download_type}_{job.get('filename', document_id)}"
        )

    except Exception as e:
        logger.exception("Download error for %s", document_id)
        return jsonify({"error": f"Download failed: {str(e)}"}), 500

@bp.get("/debug/jobs")
def debug_list_jobs():
    """Debug route to list all loaded job IDs."""
    return jsonify({
        "count": len(validation_jobs),
        "ids": list(validation_jobs.keys()),
        "store_jobs_count": len(store.validation_jobs),
        "module_name": store.__name__,
        "dict_id": id(validation_jobs),
        "store_dict_id": id(store.validation_jobs)
    })

