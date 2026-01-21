from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from server.app import create_app
from server.store import validation_jobs


@pytest.fixture
def client(tmp_path, monkeypatch):
    app = create_app()
    app.testing = True

    # Ensure corrected and uploads folders inside tmp_path to avoid polluting repo
    monkeypatch.setenv("PYTHONPATH", str(Path.cwd()))
    # Use app context
    with app.test_client() as c:
        yield c


def prepare_completed_job(document_path: Path) -> str:
    doc_id = str(uuid.uuid4())
    # Create a minimal validation_result that includes disclaimers under issues_by_category
    validation_result = {
        "total_issues": 2,
        "issues_by_category": {
            "disclaimer": [
                {
                    "issue_type": "missing_standard_disclaimer",
                    "message": "Missing capital loss disclaimer",
                    "severity": "critical",
                    "location": "Disclaimers",
                    "slide_number": None,
                }
            ]
        },
    }

    # create job record in memory
    validation_jobs[doc_id] = {
        "document_id": doc_id,
        "filename": document_path.name,
        "file_path": str(document_path),
        "status": "completed",
        "progress": 100,
        "created_at": None,
        "updated_at": None,
        "extraction_result": None,
        "validation_result": validation_result,
        "metadata": {},
        "error": None,
    }
    return doc_id


def test_fix_endpoint_applies_disclaimer_fix(client):
    # Use an example pptx from repo dataset (small sample included in repo)
    sample = Path("dataset/example_1/FINAL 47861-6PG-FR-ODDO BHF Algo Trend US-20250831.pptx")
    assert sample.exists(), "Sample PPTX for CI test must exist in repo"

    doc_id = prepare_completed_job(sample)

    resp = client.post(f"/api/v1/fix/{doc_id}", json={"fix_types": ["all"]})
    assert resp.status_code == 200, resp.get_data(as_text=True)

    body = resp.get_json()
    assert body["document_id"] == doc_id
    assert "fixes_applied" in body
    assert body["fixes_applied"] > 0, "Expected at least one fix to be applied for sample document"

