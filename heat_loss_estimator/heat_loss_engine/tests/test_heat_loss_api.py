from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

_BASE_PAYLOAD = {
    "building_id": "bld-api-test",
    "building_type": "house",
    "vision_result": {
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
            "thermal_bridge_risk_visible": "no",
        },
        "overall_confidence": 0.80,
        "needs_more_images": False,
    },
    "geometry_result": {
        "net_wall_area_m2": {"low": 120.0, "base": 150.0, "high": 180.0, "unit": "m²"},
        "roof_area_m2": {"low": 80.0, "base": 92.0, "high": 105.0, "unit": "m²"},
        "window_area_m2": {"low": 20.0, "base": 28.0, "high": 36.0, "unit": "m²"},
        "heated_volume_m3": {"low": 340.0, "base": 400.0, "high": 460.0, "unit": "m³"},
        "confidence": 0.75,
        "warnings": [],
    },
    "temperature_scenario": {
        "indoor_temp_c": 20.0,
        "outdoor_temp_c": -10.0,
    },
}


class TestHeatLossEndpoint:
    def test_returns_200(self) -> None:
        resp = client.post("/heat-loss/calculate", json=_BASE_PAYLOAD)
        assert resp.status_code == 200

    def test_response_has_building_id(self) -> None:
        body = client.post("/heat-loss/calculate", json=_BASE_PAYLOAD).json()
        assert body["building_id"] == "bld-api-test"

    def test_response_structure(self) -> None:
        body = client.post("/heat-loss/calculate", json=_BASE_PAYLOAD).json()
        assert "selected_model" in body
        assert "component_losses" in body
        assert "summary" in body
        assert "warnings" in body
        assert "disclaimers" in body

    def test_four_components_in_response(self) -> None:
        body = client.post("/heat-loss/calculate", json=_BASE_PAYLOAD).json()
        components = {c["component"] for c in body["component_losses"]}
        assert components == {"walls", "roof", "windows", "infiltration"}

    def test_summary_total_positive(self) -> None:
        body = client.post("/heat-loss/calculate", json=_BASE_PAYLOAD).json()
        assert body["summary"]["total_loss_w_base"] > 0

    def test_summary_ranges_ordered(self) -> None:
        body = client.post("/heat-loss/calculate", json=_BASE_PAYLOAD).json()
        s = body["summary"]
        assert s["total_loss_w_low"] <= s["total_loss_w_base"] <= s["total_loss_w_high"]

    def test_accepts_full_aggregated_vision_result(self) -> None:
        """Endpoint must accept the full AggregatedVisionResult from vision-service."""
        payload = dict(_BASE_PAYLOAD)
        payload["vision_result"] = {
            **_BASE_PAYLOAD["vision_result"],
            "wall_finish_material": "plaster",
            "wall_structure_guess": "brick",
            "roof_covering_material": "ceramic_tile",
            "roof_type": "gable",
            "window_type_guess": "double_glazed",
            "visible_insulation_signs": "uncertain",
            "overall_confidence": 0.75,
            "evidence": ["some evidence"],
            "needs_more_images": False,
            "missing_views": [],
            "quality_warnings": [],
            "assumption_notes": [],
        }
        resp = client.post("/heat-loss/calculate", json=payload)
        assert resp.status_code == 200

    def test_accepts_full_geometry_estimate(self) -> None:
        """Endpoint must accept the full GeometryEstimate from geometry-service."""
        payload = dict(_BASE_PAYLOAD)
        payload["geometry_result"] = {
            **_BASE_PAYLOAD["geometry_result"],
            "footprint_area_m2": {"low": 78.0, "base": 80.0, "high": 82.0, "unit": "m²"},
            "perimeter_m": {"low": 34.0, "base": 36.0, "high": 38.0, "unit": "m"},
            "facade_height_m": {"low": 5.2, "base": 5.4, "high": 5.6, "unit": "m"},
            "gross_wall_area_m2": {"low": 177.0, "base": 194.0, "high": 212.0, "unit": "m²"},
            "assumptions": {
                "assumed_floors_count": 2,
                "assumed_floor_height_m": {"low": 2.4, "base": 2.7, "high": 3.0, "unit": "m"},
                "assumed_window_to_wall_ratio": {"low": 0.11, "base": 0.18, "high": 0.25, "unit": "ratio"},
                "assumed_roof_slope_deg": {"low": 22.5, "base": 30.0, "high": 37.5, "unit": "deg"},
                "assumption_notes": [],
            },
        }
        resp = client.post("/heat-loss/calculate", json=payload)
        assert resp.status_code == 200

    def test_with_airtightness_override(self) -> None:
        payload = dict(_BASE_PAYLOAD)
        payload["airtightness_override"] = {
            "ach_low": 0.2,
            "ach_base": 0.3,
            "ach_high": 0.5,
            "source": "blower door test result",
        }
        resp = client.post("/heat-loss/calculate", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        inf = next(c for c in body["component_losses"] if c["component"] == "infiltration")
        assert "blower door" in inf["assumptions"][4]

    def test_default_temperature_scenario(self) -> None:
        payload = {k: v for k, v in _BASE_PAYLOAD.items() if k != "temperature_scenario"}
        resp = client.post("/heat-loss/calculate", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["summary"]["delta_t_c"] == 30.0

    def test_invalid_building_type_returns_422(self) -> None:
        payload = dict(_BASE_PAYLOAD)
        payload["building_type"] = "barn"
        resp = client.post("/heat-loss/calculate", json=payload)
        assert resp.status_code == 422

    def test_missing_geometry_fields_returns_422(self) -> None:
        payload = dict(_BASE_PAYLOAD)
        payload["geometry_result"] = {"confidence": 0.5}
        resp = client.post("/heat-loss/calculate", json=payload)
        assert resp.status_code == 422

    def test_disclaimers_in_response(self) -> None:
        body = client.post("/heat-loss/calculate", json=_BASE_PAYLOAD).json()
        assert len(body["disclaimers"]) >= 4
        assert any("pre-estimate" in d.lower() for d in body["disclaimers"])
