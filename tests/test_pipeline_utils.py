import json
from pathlib import Path

import pytest

from src.extractors.pipeline import ExtractionPipeline, PIPELINE_VERSION


@pytest.fixture
def pipeline(tmp_path):
    return ExtractionPipeline(use_llm=False, output_dir=tmp_path)


def test_normalize_metadata_trims_strings_and_sets_version(pipeline):
    metadata = {
        "filename": " doc.pptx ",
        "fund_name": "  Example Fund  ",
        "numeric": 5,
    }

    normalized = pipeline._normalize_metadata(metadata)

    assert normalized["filename"] == "doc.pptx"
    assert normalized["fund_name"] == "Example Fund"
    assert normalized["numeric"] == 5
    assert normalized["pipeline_version"] == PIPELINE_VERSION


def test_validate_extraction_flags_empty_and_short_text(pipeline):
    validation_empty = pipeline._validate_extraction({"text": ""})
    assert any("No text" in warning for warning in validation_empty["warnings"])

    validation_short = pipeline._validate_extraction({"text": "abc", "total_tables": 0})
    assert any("very short" in warning for warning in validation_short["warnings"])

    validation_tables = pipeline._validate_extraction({
        "text": "Valid text content" * 20,
        "tables": [],
        "total_tables": 2,
    })
    assert any("Table count mismatch" in warning for warning in validation_tables["warnings"])


def test_append_index_entry_overwrites_previous_entries(pipeline, tmp_path):
    manifest_payload_v1 = {
        "document_id": "123",
        "original_filename": "doc.pptx",
        "processed_at": "2025-01-01T00:00:00Z",
        "paths": {
            "manifest": "123/manifest.json",
            "metadata": "123/metadata.json",
            "extraction": "123/extraction.json",
            "features": None,
        },
        "summary": {"steps_completed": ["metadata"]},
    }

    manifest_payload_v2 = {
        **manifest_payload_v1,
        "processed_at": "2025-01-02T00:00:00Z",
        "summary": {"steps_completed": ["metadata", "content_extraction"]},
    }

    pipeline._append_index_entry(manifest_payload_v1)
    pipeline._append_index_entry(manifest_payload_v2)

    index_path = Path(pipeline.output_dir) / "index.jsonl"
    lines = index_path.read_text(encoding="utf-8").strip().splitlines()

    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["processed_at"] == "2025-01-02T00:00:00Z"
    assert entry["summary"]["steps_completed"] == ["metadata", "content_extraction"]
