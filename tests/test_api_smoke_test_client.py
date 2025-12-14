from __future__ import annotations

import io

import pytest

from server.app import create_app


@pytest.fixture()
def client():
    app = create_app()
    app.config.update({"TESTING": True})
    return app.test_client()


def test_health(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "healthy"


def test_upload_accepts_legacy_file_field(client):
    data = {
        "file": (io.BytesIO(b"fake pptx content"), "example.pptx"),
        "metadata": "{}",
    }

    resp = client.post("/api/v1/upload", data=data, content_type="multipart/form-data")
    assert resp.status_code == 201
    payload = resp.get_json()
    # Upload creates a job in PENDING state; validation runs via /validate.
    assert payload["status"] == "pending"
    assert "document_id" in payload


def test_report_missing_doc_is_404(client):
    resp = client.get("/api/v1/report/does-not-exist?format=json")
    assert resp.status_code == 404


def test_results_missing_doc_is_404(client):
    resp = client.get("/api/v1/results/does-not-exist")
    assert resp.status_code == 404
