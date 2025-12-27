from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Dict

from .constants import ValidationStatus


import json
import os
from pathlib import Path

# In-memory storage for validation jobs
validation_jobs: Dict[str, Dict[str, Any]] = {}
PERSISTENCE_FILE = "jobs_persistence.json"

def _save_jobs():
    """Save jobs to disk for persistence across restarts."""
    try:
        with open(PERSISTENCE_FILE, "w", encoding="utf-8") as f:
            json.dump(validation_jobs, f, indent=2)
    except Exception as e:
        print(f"Warning: Failed to save jobs persistence: {e}")

def load_jobs():
    """Load jobs from disk on startup."""
    global validation_jobs
    if os.path.exists(PERSISTENCE_FILE):
        try:
            with open(PERSISTENCE_FILE, "r", encoding="utf-8") as f:
                validation_jobs = json.load(f)
            print(f"Loaded {len(validation_jobs)} jobs from persistence.")
        except Exception as e:
            print(f"Warning: Failed to load jobs persistence: {e}")

def create_job_record(document_id: str, filename: str, file_path: str) -> Dict[str, Any]:
    job = {
        "document_id": document_id,
        "filename": filename,
        "file_path": file_path,
        "status": ValidationStatus.PENDING,
        "progress": 0,
        "created_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "updated_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "extraction_result": None,
        "validation_result": None,
        "metadata": None,
        "error": None,
    }
    validation_jobs[document_id] = job
    _save_jobs()
    return job


def _convert_dates(obj: Any) -> Any:
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: _convert_dates(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convert_dates(item) for item in obj]
    return obj


def update_job_status(document_id: str, status: str, progress: int | None = None, **kwargs: Any) -> None:
    if document_id not in validation_jobs:
        return

    job = validation_jobs[document_id]
    job["status"] = status
    job["updated_at"] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    if progress is not None:
        job["progress"] = progress

    for key, value in kwargs.items():
        job[key] = _convert_dates(value)
    
    _save_jobs()
