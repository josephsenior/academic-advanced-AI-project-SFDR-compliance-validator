from __future__ import annotations

import hashlib
import json
import logging
import uuid
from pathlib import Path
from typing import Any

from flask import current_app, jsonify, request
from werkzeug.utils import secure_filename

from ...constants import ALLOWED_EXTENSIONS, ValidationStatus
from server.store import create_job_record, validation_jobs

from . import bp

logger = logging.getLogger(__name__)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS




def get_file_hash(file_stream) -> str:
    """Calculate SHA-256 hash of a file-like object."""
    hasher = hashlib.sha256()
    # Read in chunks to be memory efficient
    for chunk in iter(lambda: file_stream.read(4096), b""):
        hasher.update(chunk)
    file_stream.seek(0) # IMPORTANT: Seek back to start after reading
    return hasher.hexdigest()

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
            return (
                jsonify({"error": f"Document file type not supported. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"}),
                400,
            )

        # Calculate hash to identify unique documents
        file_hash = get_file_hash(document_file)
        # Use first 16 chars of hash combined with a short uuid fragment to ensure uniqueness but stable matching
        # Or just use the hash if we want to "match" exactly.
        # User wants "matching with current document". Let's use hash directly if possible, or allow lookup.
        
        # Check if hash already exists in store
        existing_id = None
        for job_id, job in validation_jobs.items():
            if job.get("file_hash") == file_hash:
                existing_id = job_id
                break
        
        if existing_id:
            logger.info("Matching existing document found for hash %s: %s", file_hash[:10], existing_id)
            document_id = existing_id
        else:
            document_id = str(uuid.uuid4())

        doc_dir = Path(current_app.config["UPLOAD_FOLDER"]) / document_id
        doc_dir.mkdir(parents=True, exist_ok=True)

        filename = secure_filename(document_file.filename)
        file_path = doc_dir / filename
        document_file.save(file_path)

        metadata: Any = None
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
        prospectus_file = request.files.get("prospectus")
        if prospectus_file and prospectus_file.filename:
            prospectus_filename = secure_filename(prospectus_file.filename)
            prospectus_path = doc_dir / f"prospectus_{prospectus_filename}"
            prospectus_file.save(prospectus_path)
            has_prospectus = True
            logger.info("Prospectus uploaded for %s: %s", document_id, prospectus_filename)


        job = create_job_record(document_id, filename, str(file_path))
        job["file_hash"] = file_hash
        job["metadata"] = metadata
        job["has_prospectus"] = has_prospectus
        print(f"DEBUG: UPLOAD adding {document_id}. dict id: {id(validation_jobs)}, len: {len(validation_jobs)}")
        validation_jobs[document_id] = job
        print(f"DEBUG: UPLOAD after add. len: {len(validation_jobs)}")
        
        # If we reused an ID, we might have overwritten the record, but that's okay.
        # Ensure _save_jobs is called
        from server.store import _save_jobs
        _save_jobs()

        logger.info(
            "Upload complete: %s - %s (metadata: %s, prospectus: %s)",
            document_id,
            filename,
            has_metadata,
            has_prospectus,
        )

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
