from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Dict

from .constants import ValidationStatus


import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

# In-memory storage for validation jobs
validation_jobs: Dict[str, Dict[str, Any]] = {}
PERSISTENCE_FILE = "jobs_persistence.json"

def _convert_to_serializable(obj: Any) -> Any:
    """Recursively convert objects to JSON-serializable formats."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if hasattr(obj, "to_dict"):
        return _convert_to_serializable(obj.to_dict())
    if hasattr(obj, "__dict__"):
        return _convert_to_serializable(obj.__dict__)
    if isinstance(obj, dict):
        return {str(k): _convert_to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convert_to_serializable(item) for item in obj]
    if isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    return str(obj)

def _save_jobs():
    """Save jobs to disk atomically for persistence across restarts."""
    try:
        # Create a temporary file in the same directory as the persistence file
        persist_path = Path(PERSISTENCE_FILE)
        persist_dir = persist_path.parent
        
        with NamedTemporaryFile('w', dir=persist_dir, delete=False, encoding='utf-8', suffix='.tmp') as tf:
            json.dump(_convert_to_serializable(validation_jobs), tf, indent=2)
            temp_name = tf.name
            
        # Atomic rename (on Windows this might need os.replace or first deleting the old one)
        if os.path.exists(PERSISTENCE_FILE):
            os.remove(PERSISTENCE_FILE)
        os.rename(temp_name, PERSISTENCE_FILE)
        
    except Exception as e:
        print(f"Warning: Failed to save jobs persistence: {e}")

def load_jobs():
    """Load jobs from disk on startup."""
    global validation_jobs
    if os.path.exists(PERSISTENCE_FILE):
        try:
            with open(PERSISTENCE_FILE, "r", encoding="utf-8") as f:
                loaded_jobs = json.load(f)
                validation_jobs.clear()
                validation_jobs.update(loaded_jobs)
            print(f"Loaded {len(validation_jobs)} jobs from persistence.")
            print("Job IDs in store:", list(validation_jobs.keys()))
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

def update_job_status(document_id: str, status: str, progress: int | None = None, **kwargs: Any) -> None:
    if document_id not in validation_jobs:
        return

    job = validation_jobs[document_id]
    job["status"] = status
    job["updated_at"] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    if progress is not None:
        job["progress"] = progress

    for key, value in kwargs.items():
        job[key] = value # _save_jobs will handle conversion
    
    _save_jobs()
