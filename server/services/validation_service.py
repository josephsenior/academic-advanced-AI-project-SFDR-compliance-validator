from __future__ import annotations

import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict

from flask import current_app

from ..constants import ValidationStatus
from ..serialization import DateTimeEncoder, format_validation_result
from ..store import update_job_status

logger = logging.getLogger(__name__)


def _convert_dates_for_json(obj: Any) -> Any:
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: _convert_dates_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convert_dates_for_json(item) for item in obj]
    return obj


def run_validation(document_id: str, job: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
    """Runs extraction + validation synchronously, persists outputs, updates job state."""

    # Lazy imports to keep server startup fast and avoid importing optional heavy deps
    # (LLM toolchains, transformers/numpy) until validation is actually requested.
    from backend.extractors.agents.data_consistency_agent import DataConsistencyAgent
    from backend.extractors.validators.disclaimer_validator import DisclaimerValidator
    from backend.extractors.pipeline import ExtractionPipeline

    update_job_status(document_id, ValidationStatus.EXTRACTING, 10)

    logger.info("Starting extraction for %s", document_id)
    pipeline = ExtractionPipeline()
    extraction_result = pipeline.process_document(job["file_path"])

    output_dir = Path(current_app.config["OUTPUT_FOLDER"]) / document_id
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / "extraction.json", "w", encoding="utf-8") as f:
        json.dump(extraction_result, f, indent=2, ensure_ascii=False, cls=DateTimeEncoder)

    update_job_status(document_id, ValidationStatus.VALIDATING, 50, extraction_result=extraction_result)

    logger.info("Starting validation for %s", document_id)

    disclaimer_validator = None
    if options.get("enable_disclaimers", True):
        try:
            disclaimer_validator = DisclaimerValidator()
        except Exception as e:
            logger.warning("Could not initialize disclaimer validator: %s", e)

    agent = DataConsistencyAgent(
        enable_esg_validation=options.get("enable_esg", False),
    )

    actual_extraction = extraction_result.get("extraction_result", extraction_result)
    validation_result = agent.validate(actual_extraction, job.get("metadata"))

    # Get filename from job record
    filename = job.get("filename") or Path(job["file_path"]).name
    formatted_result = format_validation_result(validation_result, job.get("metadata"), filename=filename)
    formatted_result = _convert_dates_for_json(formatted_result)

    with open(output_dir / "validation_result.json", "w", encoding="utf-8") as f:
        json.dump(formatted_result, f, indent=2, ensure_ascii=False, cls=DateTimeEncoder)

    update_job_status(document_id, ValidationStatus.COMPLETED, 100, validation_result=formatted_result)
    logger.info("Validation completed for %s: %s issues found", document_id, formatted_result.get("total_issues"))

    return formatted_result
