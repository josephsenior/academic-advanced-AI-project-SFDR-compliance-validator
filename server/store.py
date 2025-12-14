from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict

from .constants import ValidationStatus


# In-memory storage for validation jobs (use Redis/DB in production)
validation_jobs: Dict[str, Dict[str, Any]] = {}


def create_job_record(document_id: str, filename: str, file_path: str) -> Dict[str, Any]:
    return {
        "document_id": document_id,
        "filename": filename,
        "file_path": file_path,
        "status": ValidationStatus.PENDING,
        "progress": 0,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "extraction_result": None,
        "validation_result": None,
        "metadata": None,
        "error": None,
    }


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
    job["updated_at"] = datetime.utcnow().isoformat()
    if progress is not None:
        job["progress"] = progress

    for key, value in kwargs.items():
        job[key] = _convert_dates(value)
