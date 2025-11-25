import json
from pathlib import Path

import pytest

from src.extractors.pipeline import ExtractionPipeline


@pytest.fixture
def fixtures():
    base = Path("tests/golden")
    extraction = json.load((base / "extraction_fixture.json").open("r", encoding="utf-8"))
    metadata = json.load((base / "metadata_fixture.json").open("r", encoding="utf-8"))
    expected = json.load((base / "expected_summary.json").open("r", encoding="utf-8"))
    return extraction, metadata, expected


def test_pipeline_golden(monkeypatch, tmp_path, fixtures):
    extraction_fixture, metadata_fixture, expected = fixtures

    output_dir = tmp_path / "outputs"
    pipeline = ExtractionPipeline(use_llm=False, output_dir=str(output_dir))

    # Monkeypatch extractor and metadata layers to return fixtures without touching real files.
    monkeypatch.setattr(pipeline.document_extractor, "extract", lambda _: extraction_fixture)

    def fake_metadata_extract(file_path, metadata_json_path=None):
        meta = dict(metadata_fixture)
        meta.setdefault('filename', Path(file_path).name)
        meta.setdefault('file_path', str(Path(file_path)))
        meta.setdefault('file_directory', str(Path(file_path).parent))
        meta.setdefault('extracted_at', '2025-01-01T00:00:00')
        return meta

    monkeypatch.setattr(pipeline.metadata_extractor, "extract", fake_metadata_extract)

    dummy_file = tmp_path / "dummy.txt"
    dummy_file.write_text("placeholder", encoding="utf-8")

    result = pipeline.process_document(str(dummy_file))

    assert result['executive_summary'] == expected['executive_summary']
    assert result['metadata']['disclaimer_glossary_matches']
    assert result['metadata']['performance_table_entries'][0]['value'] == 10.0
    assert result['metadata']['is_new_product'] is False
    assert result['metadata']['is_sicav_product'] is True
