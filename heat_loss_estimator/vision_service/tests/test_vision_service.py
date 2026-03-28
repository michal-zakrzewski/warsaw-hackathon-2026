from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.clients.vision_model_client import FakeVisionModelClient
from app.dependencies import get_vision_client
from app.domain.vision_models import (
    ImageInput,
    PerImageVisionResult,
    VisionRequest,
    VisionResponse,
)
from app.services.vision_service import VisionService
from main import app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_image(image_id: str, view_type: str = "front") -> ImageInput:
    return ImageInput(
        image_id=image_id,
        source_type="upload",
        storage_path=f"/uploads/{image_id}.jpg",
        view_type=view_type,  # type: ignore[arg-type]
    )


def _make_request(*view_types: str) -> VisionRequest:
    return VisionRequest(
        building_id="bld-001",
        images=[
            _make_image(f"img-{i}", view_type=vt)
            for i, vt in enumerate(view_types)
        ],
        building_type_hint="house",
        country_code="PL",
    )


# ---------------------------------------------------------------------------
# Model validation
# ---------------------------------------------------------------------------


class TestImageInputValidation:
    def test_valid_upload_image(self) -> None:
        img = ImageInput(
            image_id="x1",
            source_type="upload",
            storage_path="/data/x1.jpg",
            view_type="front",
        )
        assert img.image_id == "x1"
        assert img.source_type == "upload"
        assert img.view_type == "front"

    def test_optional_fields_default_to_none(self) -> None:
        img = ImageInput(
            image_id="x2",
            source_type="url",
            image_url="https://example.com/img.jpg",
            view_type="unknown",
        )
        assert img.mime_type is None
        assert img.captured_at is None
        assert img.notes is None

    def test_invalid_source_type_raises(self) -> None:
        with pytest.raises(Exception):
            ImageInput(
                image_id="x3",
                source_type="ftp",  # type: ignore[arg-type]
                view_type="front",
            )

    def test_invalid_view_type_raises(self) -> None:
        with pytest.raises(Exception):
            ImageInput(
                image_id="x4",
                source_type="upload",
                view_type="basement",  # type: ignore[arg-type]
            )


class TestVisionRequestValidation:
    def test_default_building_type_hint(self) -> None:
        req = VisionRequest(
            building_id="b1",
            images=[_make_image("i1")],
        )
        assert req.building_type_hint == "unknown"

    def test_explicit_building_type_hint(self) -> None:
        req = VisionRequest(
            building_id="b2",
            images=[_make_image("i1")],
            building_type_hint="apartment_block",
        )
        assert req.building_type_hint == "apartment_block"


# ---------------------------------------------------------------------------
# VisionService
# ---------------------------------------------------------------------------


class TestVisionService:
    def _service(self) -> VisionService:
        return VisionService(FakeVisionModelClient())

    def test_returns_vision_response(self) -> None:
        req = _make_request("front", "roof_oblique")
        result = self._service().analyze(req)
        assert isinstance(result, VisionResponse)
        assert result.building_id == "bld-001"

    def test_per_image_count_matches_input(self) -> None:
        req = _make_request("front", "side", "roof_oblique")
        result = self._service().analyze(req)
        assert len(result.per_image_results) == 3

    def test_per_image_ids_match(self) -> None:
        req = _make_request("front", "side")
        result = self._service().analyze(req)
        returned_ids = {r.image_id for r in result.per_image_results}
        expected_ids = {img.image_id for img in req.images}
        assert returned_ids == expected_ids

    def test_per_image_result_shape(self) -> None:
        req = _make_request("front")
        result = self._service().analyze(req)
        r: PerImageVisionResult = result.per_image_results[0]
        assert 0.0 <= r.confidence <= 1.0
        assert isinstance(r.evidence, list)
        assert isinstance(r.missing_information, list)

    def test_front_view_has_roof_not_visible(self) -> None:
        req = _make_request("front")
        result = self._service().analyze(req)
        assert result.per_image_results[0].image_quality_flags.roof_not_visible is True

    def test_roof_oblique_view_has_facade_not_visible(self) -> None:
        req = _make_request("roof_oblique")
        result = self._service().analyze(req)
        assert result.per_image_results[0].image_quality_flags.facade_not_visible is True

    def test_single_front_image_needs_more_images(self) -> None:
        """Only a front view → roof view missing → needs_more_images."""
        req = _make_request("front")
        result = self._service().analyze(req)
        assert result.aggregated.needs_more_images is True

    def test_complete_view_set_does_not_need_more_images(self) -> None:
        req = _make_request("front", "side", "roof_oblique")
        result = self._service().analyze(req)
        assert result.aggregated.needs_more_images is False


# ---------------------------------------------------------------------------
# FastAPI endpoint
# ---------------------------------------------------------------------------


class TestVisionEndpoint:
    @pytest.fixture(autouse=True)
    def override_client(self) -> None:
        app.dependency_overrides[get_vision_client] = lambda: FakeVisionModelClient()
        yield
        app.dependency_overrides.clear()

    @pytest.fixture
    def client(self) -> TestClient:
        return TestClient(app)

    def test_analyze_returns_200(self, client: TestClient) -> None:
        payload = {
            "building_id": "bld-test",
            "images": [
                {
                    "image_id": "img-1",
                    "source_type": "upload",
                    "storage_path": "/uploads/img-1.jpg",
                    "view_type": "front",
                }
            ],
        }
        resp = client.post("/vision/analyze", json=payload)
        assert resp.status_code == 200

    def test_analyze_response_structure(self, client: TestClient) -> None:
        payload = {
            "building_id": "bld-test",
            "images": [
                {
                    "image_id": "img-1",
                    "source_type": "upload",
                    "storage_path": "/uploads/img-1.jpg",
                    "view_type": "front",
                },
                {
                    "image_id": "img-2",
                    "source_type": "upload",
                    "storage_path": "/uploads/img-2.jpg",
                    "view_type": "roof_oblique",
                },
            ],
            "building_type_hint": "house",
            "country_code": "PL",
        }
        resp = client.post("/vision/analyze", json=payload)
        body = resp.json()
        assert body["building_id"] == "bld-test"
        assert len(body["per_image_results"]) == 2
        agg = body["aggregated"]
        assert "wall_finish_material" in agg
        assert "overall_confidence" in agg
        assert "needs_more_images" in agg
        assert isinstance(agg["missing_views"], list)

    def test_invalid_payload_returns_422(self, client: TestClient) -> None:
        resp = client.post("/vision/analyze", json={"building_id": "x"})
        assert resp.status_code == 422
