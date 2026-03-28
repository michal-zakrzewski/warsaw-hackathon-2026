from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient

from app.api.bill_intelligence import router, _get_client
from app.clients.documentai_client import FakeDocumentAIClient
from main import app


@pytest.fixture(autouse=True)
def use_fake_client():
    app.dependency_overrides[_get_client] = lambda: FakeDocumentAIClient()
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _three_doc_payload() -> dict:
    return {
        "building_id": "bld-warsaw-001",
        "country_code": "PL",
        "annualization_mode": "normalize_to_365",
        "allow_fallback_processor": True,
        "documents": [
            {
                "document_id": f"bill-2024-{i:02d}",
                "source_type": "local_file",
                "file_path": f"/fake/path/bill-2024-{i:02d}.pdf",
                "mime_type": "application/pdf",
                "file_name": f"bill-2024-{i:02d}.pdf",
            }
            for i in range(1, 4)
        ],
    }


class TestProcessEndpoint:
    def test_returns_200(self, client: TestClient):
        resp = client.post("/bill-intelligence/process", json=_three_doc_payload())
        assert resp.status_code == 200

    def test_response_structure(self, client: TestClient):
        resp = client.post("/bill-intelligence/process", json=_three_doc_payload())
        body = resp.json()
        assert body["building_id"] == "bld-warsaw-001"
        assert len(body["extractions"]) == 3
        assert len(body["normalized_bills"]) == 3
        assert "portfolio_summary" in body
        assert "derived_inputs" in body

    def test_extractions_are_successful(self, client: TestClient):
        resp = client.post("/bill-intelligence/process", json=_three_doc_payload())
        for ext in resp.json()["extractions"]:
            assert ext["success"] is True
            assert ext["confidence"] > 0

    def test_normalized_bills_have_kwh(self, client: TestClient):
        resp = client.post("/bill-intelligence/process", json=_three_doc_payload())
        for bill in resp.json()["normalized_bills"]:
            assert bill["electricity_import_kwh"] is not None
            assert bill["electricity_import_kwh"] > 0

    def test_derived_inputs_present(self, client: TestClient):
        resp = client.post("/bill-intelligence/process", json=_three_doc_payload())
        di = resp.json()["derived_inputs"]
        assert di["annual_electricity_kwh"] is not None
        assert di["annual_bill_cost"] is not None
        assert di["confidence"] > 0

    def test_invalid_payload_returns_422(self, client: TestClient):
        resp = client.post("/bill-intelligence/process", json={"building_id": "x"})
        assert resp.status_code == 422
