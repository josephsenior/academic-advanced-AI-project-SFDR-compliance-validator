from __future__ import annotations

from dataclasses import dataclass
import logging


ALLOWED_EXTENSIONS = {"pptx", "pdf", "docx"}


class ValidationStatus:
    PENDING = "pending"
    UPLOADING = "uploading"
    EXTRACTING = "extracting"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class ApiConfig:
    max_content_length_bytes: int = 100 * 1024 * 1024
    upload_folder: str = "uploads"
    output_folder: str = "outputs"
    corrected_folder: str = "corrected_documents"
    api_prefix: str = "/api/v1"
    log_level: int = logging.INFO
