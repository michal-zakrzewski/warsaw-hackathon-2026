from __future__ import annotations

import pytest

from app.domain.geometry_models import (
    BuildingDimensionsHint,
    GeometryRequest,
    GeometryResponse,
    RangeValue,
    VisionResultInput,
)
from app.services.geometry_service import estimate_geometry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _good_vision(
    roof_type: str = "gable",
    window_type: str = "double_glazed",
    confidence: float = 0.80,
    needs_more: bool = False,
) -> VisionResultInput:
    return VisionResultInput(
        roof_type=roof_type,
        window_type_guess=window_type,
        overall_confidence=confidence,
        needs_more_images=needs_more,
    )


def _request(
    building_type: str = "house",
    vision: VisionResultInput | None = None,
    **hint_kwargs,
) -> GeometryRequest:
    return GeometryRequest(
        building_id="bld-test",
        building_type=building_type,  # type: ignore[arg-type]
        vision_result=vision or _good_vision(),
        dimensions_hint=BuildingDimensionsHint(**hint_kwargs),
    )


def _is_valid_range(rv: RangeValue) -> bool:
    return rv.low <= rv.base <= rv.high and rv.low >= 0


# ---------------------------------------------------------------------------
# Single family house with full footprint dimensions
# ---------------------------------------------------------------------------


class TestHouseWithDimensions:
    def test_returns_geometry_response(self) -> None:
        resp = estimate_geometry(
            _request("house", building_length_m=10.0, building_width_m=8.0, floors_count=2)
        )
        assert isinstance(resp, GeometryResponse)
        assert resp.building_id == "bld-test"

    def test_footprint_matches_l_times_w(self) -> None:
        resp = estimate_geometry(
            _request("house", building_length_m=10.0, building_width_m=8.0, floors_count=2)
        )
        fp = resp.estimate.footprint_area_m2
        assert abs(fp.base - 80.0) < 0.5
        # Tight range when dimensions are given
        assert (fp.high - fp.low) / fp.base < 0.10

    def test_perimeter_matches_2lwl_plus_w(self) -> None:
        resp = estimate_geometry(
            _request("house", building_length_m=10.0, building_width_m=8.0, floors_count=2)
        )
        assert abs(resp.estimate.perimeter_m.base - 36.0) < 1.0

    def test_all_ranges_are_valid(self) -> None:
        resp = estimate_geometry(
            _request("house", building_length_m=10.0, building_width_m=8.0, floors_count=2)
        )
        e = resp.estimate
        for rv in [
            e.footprint_area_m2,
            e.perimeter_m,
            e.facade_height_m,
            e.gross_wall_area_m2,
            e.window_area_m2,
            e.net_wall_area_m2,
            e.roof_area_m2,
            e.heated_volume_m3,
        ]:
            assert _is_valid_range(rv), f"Invalid range: {rv}"

    def test_net_wall_less_than_gross_wall(self) -> None:
        resp = estimate_geometry(
            _request("house", building_length_m=10.0, building_width_m=8.0, floors_count=2)
        )
        e = resp.estimate
        assert e.net_wall_area_m2.base < e.gross_wall_area_m2.base

    def test_window_area_plus_net_wall_approximately_equals_gross(self) -> None:
        resp = estimate_geometry(
            _request("house", building_length_m=10.0, building_width_m=8.0, floors_count=2)
        )
        e = resp.estimate
        assert abs(
            e.net_wall_area_m2.base + e.window_area_m2.base - e.gross_wall_area_m2.base
        ) < 0.5

    def test_confidence_is_high_with_full_data(self) -> None:
        resp = estimate_geometry(
            _request(
                "house",
                building_length_m=10.0,
                building_width_m=8.0,
                floors_count=2,
                floor_height_m=2.7,
                window_to_wall_ratio_hint=0.20,
            )
        )
        assert resp.estimate.confidence >= 0.70


# ---------------------------------------------------------------------------
# Building with footprint_area only
# ---------------------------------------------------------------------------


class TestBuildingWithFootprintOnly:
    def test_footprint_close_to_provided_value(self) -> None:
        resp = estimate_geometry(
            _request("apartment_block", footprint_area_m2=400.0, floors_count=5)
        )
        assert abs(resp.estimate.footprint_area_m2.base - 400.0) < 1.0

    def test_perimeter_range_is_wider_than_with_lw(self) -> None:
        resp_lw = estimate_geometry(
            _request("apartment_block", building_length_m=40.0, building_width_m=10.0, floors_count=5)
        )
        resp_fp = estimate_geometry(
            _request("apartment_block", footprint_area_m2=400.0, floors_count=5)
        )
        lw_spread = resp_lw.estimate.perimeter_m.high - resp_lw.estimate.perimeter_m.low
        fp_spread = resp_fp.estimate.perimeter_m.high - resp_fp.estimate.perimeter_m.low
        assert fp_spread > lw_spread

    def test_assumption_note_mentions_rectangular(self) -> None:
        resp = estimate_geometry(
            _request("apartment_block", footprint_area_m2=400.0, floors_count=5)
        )
        notes = resp.estimate.assumptions.assumption_notes
        assert any("rectangular" in n.lower() for n in notes)


# ---------------------------------------------------------------------------
# Minimal input — only building type
# ---------------------------------------------------------------------------


class TestMinimalInput:
    def test_produces_valid_response(self) -> None:
        resp = estimate_geometry(_request("house"))
        e = resp.estimate
        assert _is_valid_range(e.footprint_area_m2)
        assert _is_valid_range(e.roof_area_m2)

    def test_warns_about_missing_footprint(self) -> None:
        resp = estimate_geometry(_request("house"))
        assert any("footprint" in w.lower() for w in resp.estimate.warnings)

    def test_warns_about_assumed_floors(self) -> None:
        resp = estimate_geometry(_request("house"))
        assert any("floor" in w.lower() for w in resp.estimate.warnings)

    def test_confidence_is_low(self) -> None:
        resp = estimate_geometry(_request("house"))
        assert resp.estimate.confidence < 0.65

    def test_ranges_are_wider_than_with_data(self) -> None:
        minimal = estimate_geometry(_request("house"))
        full = estimate_geometry(
            _request(
                "house",
                building_length_m=10.0,
                building_width_m=8.0,
                floors_count=2,
                floor_height_m=2.7,
            )
        )
        minimal_fp_spread = (
            minimal.estimate.footprint_area_m2.high
            - minimal.estimate.footprint_area_m2.low
        )
        full_fp_spread = (
            full.estimate.footprint_area_m2.high - full.estimate.footprint_area_m2.low
        )
        assert minimal_fp_spread > full_fp_spread


# ---------------------------------------------------------------------------
# Roof types
# ---------------------------------------------------------------------------


class TestRoofTypes:
    @pytest.mark.parametrize("roof_type", ["flat", "gable", "hip", "shed", "mansard", "sawtooth", "unknown"])
    def test_all_roof_types_produce_valid_ranges(self, roof_type: str) -> None:
        resp = estimate_geometry(
            _request(
                "house",
                building_length_m=10.0,
                building_width_m=8.0,
                floors_count=2,
                vision=_good_vision(roof_type=roof_type),
            )
        )
        assert _is_valid_range(resp.estimate.roof_area_m2)

    def test_flat_roof_area_equals_footprint(self) -> None:
        resp = estimate_geometry(
            _request(
                "house",
                building_length_m=10.0,
                building_width_m=8.0,
                floors_count=2,
                vision=_good_vision(roof_type="flat"),
            )
        )
        fp = resp.estimate.footprint_area_m2.base
        roof = resp.estimate.roof_area_m2.base
        assert abs(roof - fp) < 0.5

    def test_pitched_roof_area_larger_than_footprint(self) -> None:
        for rtype in ("gable", "hip", "mansard"):
            resp = estimate_geometry(
                _request(
                    "house",
                    building_length_m=10.0,
                    building_width_m=8.0,
                    floors_count=2,
                    vision=_good_vision(roof_type=rtype),
                )
            )
            assert resp.estimate.roof_area_m2.base > resp.estimate.footprint_area_m2.base

    def test_unknown_roof_type_adds_warning(self) -> None:
        resp = estimate_geometry(
            _request("house", vision=_good_vision(roof_type="unknown"))
        )
        assert any("roof type unknown" in w.lower() for w in resp.estimate.warnings)

    def test_mansard_roof_adds_warning(self) -> None:
        resp = estimate_geometry(
            _request("house", vision=_good_vision(roof_type="mansard"))
        )
        assert any("mansard" in w.lower() for w in resp.estimate.warnings)


# ---------------------------------------------------------------------------
# Range propagation
# ---------------------------------------------------------------------------


class TestRangePropagation:
    def test_user_wwr_produces_narrower_window_range(self) -> None:
        with_hint = estimate_geometry(
            _request(
                "house",
                building_length_m=10.0,
                building_width_m=8.0,
                floors_count=2,
                window_to_wall_ratio_hint=0.20,
            )
        )
        without_hint = estimate_geometry(
            _request("house", building_length_m=10.0, building_width_m=8.0, floors_count=2)
        )
        spread_with = (
            with_hint.estimate.window_area_m2.high
            - with_hint.estimate.window_area_m2.low
        )
        spread_without = (
            without_hint.estimate.window_area_m2.high
            - without_hint.estimate.window_area_m2.low
        )
        assert spread_with < spread_without

    def test_heated_volume_hint_is_used_when_provided(self) -> None:
        resp = estimate_geometry(
            _request("house", building_length_m=10.0, building_width_m=8.0, floors_count=2, heated_volume_m3_hint=450.0)
        )
        assert abs(resp.estimate.heated_volume_m3.base - 450.0) < 5.0

    def test_volume_hint_range_is_tight(self) -> None:
        resp = estimate_geometry(
            _request("house", heated_volume_m3_hint=400.0)
        )
        spread = resp.estimate.heated_volume_m3.high - resp.estimate.heated_volume_m3.low
        assert spread / 400.0 < 0.15


# ---------------------------------------------------------------------------
# Warnings on missing data
# ---------------------------------------------------------------------------


class TestWarnings:
    def test_low_vision_confidence_adds_warning(self) -> None:
        resp = estimate_geometry(
            _request("house", vision=_good_vision(confidence=0.40))
        )
        assert any("confidence" in w.lower() for w in resp.estimate.warnings)

    def test_vision_needs_more_images_adds_warning(self) -> None:
        resp = estimate_geometry(
            _request("house", vision=_good_vision(needs_more=True))
        )
        assert any("more" in w.lower() for w in resp.estimate.warnings)

    def test_unknown_building_type_adds_warning(self) -> None:
        resp = estimate_geometry(_request("unknown"))
        assert any("unknown" in w.lower() for w in resp.estimate.warnings)

    def test_no_spurious_warnings_with_full_data(self) -> None:
        resp = estimate_geometry(
            _request(
                "house",
                building_length_m=10.0,
                building_width_m=8.0,
                floors_count=2,
                floor_height_m=2.7,
                window_to_wall_ratio_hint=0.20,
                vision=_good_vision(needs_more=False, confidence=0.85),
            )
        )
        # Should not warn about missing footprint, floors, or vision quality
        text = " ".join(resp.estimate.warnings).lower()
        assert "footprint" not in text
        assert "floor" not in text
        assert "confidence" not in text


# ---------------------------------------------------------------------------
# Building-type defaults sanity checks
# ---------------------------------------------------------------------------


class TestBuildingTypeDefaults:
    @pytest.mark.parametrize("btype", ["house", "apartment_block", "office", "warehouse", "industrial", "unknown"])
    def test_all_types_produce_valid_estimate(self, btype: str) -> None:
        resp = estimate_geometry(_request(btype))
        e = resp.estimate
        for rv in [
            e.footprint_area_m2,
            e.facade_height_m,
            e.gross_wall_area_m2,
            e.roof_area_m2,
            e.heated_volume_m3,
        ]:
            assert _is_valid_range(rv)

    def test_warehouse_has_high_floor_height(self) -> None:
        resp = estimate_geometry(_request("warehouse"))
        assert resp.estimate.assumptions.assumed_floor_height_m.base >= 4.0

    def test_office_has_higher_wwr_than_house(self) -> None:
        house = estimate_geometry(_request("house"))
        office = estimate_geometry(_request("office"))
        assert (
            office.estimate.assumptions.assumed_window_to_wall_ratio.base
            > house.estimate.assumptions.assumed_window_to_wall_ratio.base
        )
