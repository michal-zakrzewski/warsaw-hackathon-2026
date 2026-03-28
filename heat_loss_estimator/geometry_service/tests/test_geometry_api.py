from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

_BASE_PAYLOAD = {
    "building_id": "bld-api-test",
    "building_type": "house",
    "vision_result": {
        "roof_type": "gable",
        "window_type_guess": "double_glazed",
        "overall_confidence": 0.80,
        "needs_more_images": False,
    },
    "dimensions_hint": {
        "building_length_m": 12.0,
        "building_width_m": 9.0,
        "floors_count": 2,
        "floor_height_m": 2.70,
    },
}


class TestGeometryEndpoint:
    def test_returns_200(self) -> None:
        resp = client.post("/geometry/estimate", json=_BASE_PAYLOAD)
        assert resp.status_code == 200

    def test_response_building_id(self) -> None:
        resp = client.post("/geometry/estimate", json=_BASE_PAYLOAD)
        assert resp.json()["building_id"] == "bld-api-test"

    def test_response_has_estimate_fields(self) -> None:
        body = client.post("/geometry/estimate", json=_BASE_PAYLOAD).json()
        est = body["estimate"]
        for field in [
            "footprint_area_m2",
            "perimeter_m",
            "facade_height_m",
            "gross_wall_area_m2",
            "window_area_m2",
            "net_wall_area_m2",
            "roof_area_m2",
            "heated_volume_m3",
            "confidence",
            "warnings",
            "assumptions",
        ]:
            assert field in est, f"Missing field: {field}"

    def test_range_values_have_low_base_high(self) -> None:
        body = client.post("/geometry/estimate", json=_BASE_PAYLOAD).json()
        est = body["estimate"]
        for key in ["footprint_area_m2", "perimeter_m", "roof_area_m2"]:
            rv = est[key]
            assert rv["low"] <= rv["base"] <= rv["high"]

    def test_accepts_vision_result_as_full_aggregated_json(self) -> None:
        """geometry service must accept the full AggregatedVisionResult payload."""
        payload = dict(_BASE_PAYLOAD)
        payload["vision_result"] = {
            "wall_finish_material": "plaster",
            "wall_structure_guess": "brick",
            "roof_covering_material": "ceramic_tile",
            "roof_type": "gable",
            "window_type_guess": "double_glazed",
            "visible_insulation_signs": "uncertain",
            "condition_flags": {
                "cracks_visible": "no",
                "moisture_stains_visible": "no",
                "facade_degradation_visible": "no",
                "roof_damage_visible": "no",
                "thermal_bridge_risk_visible": "uncertain",
            },
            "overall_confidence": 0.75,
            "evidence": ["Plaster facade"],
            "needs_more_images": False,
            "missing_views": [],
            "quality_warnings": [],
            "assumption_notes": [],
        }
        resp = client.post("/geometry/estimate", json=payload)
        assert resp.status_code == 200
        assert resp.json()["estimate"]["assumptions"]["assumed_roof_slope_deg"]["base"] > 0

    def test_minimal_payload_returns_200(self) -> None:
        payload = {
            "building_id": "bld-min",
            "building_type": "house",
            "vision_result": {},
            "dimensions_hint": {},
        }
        resp = client.post("/geometry/estimate", json=payload)
        assert resp.status_code == 200

    def test_invalid_building_type_returns_422(self) -> None:
        payload = dict(_BASE_PAYLOAD)
        payload["building_type"] = "castle"
        resp = client.post("/geometry/estimate", json=payload)
        assert resp.status_code == 422

    def test_negative_floors_returns_422(self) -> None:
        payload = dict(_BASE_PAYLOAD)
        payload["dimensions_hint"] = {"floors_count": -1}
        resp = client.post("/geometry/estimate", json=payload)
        assert resp.status_code == 422

    def test_wwr_above_one_returns_422(self) -> None:
        payload = dict(_BASE_PAYLOAD)
        payload["dimensions_hint"] = {"window_to_wall_ratio_hint": 1.5}
        resp = client.post("/geometry/estimate", json=payload)
        assert resp.status_code == 422
