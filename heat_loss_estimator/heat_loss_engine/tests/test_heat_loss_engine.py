from __future__ import annotations

import pytest

from app.domain.heat_loss_models import (
    AirtightnessAssumption,
    ConditionFlagsInput,
    GeometryInput,
    HeatLossRequest,
    HeatLossResponse,
    RangeValueInput,
    TemperatureScenario,
    VisionInput,
)
from app.services.heat_loss_engine import calculate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _rv(low: float, base: float, high: float) -> RangeValueInput:
    return RangeValueInput(low=low, base=base, high=high)


def _geometry(
    net_wall: tuple[float, float, float] = (120.0, 150.0, 180.0),
    roof: tuple[float, float, float] = (80.0, 92.0, 105.0),
    window: tuple[float, float, float] = (20.0, 28.0, 36.0),
    volume: tuple[float, float, float] = (340.0, 400.0, 460.0),
    confidence: float = 0.75,
) -> GeometryInput:
    return GeometryInput(
        net_wall_area_m2=_rv(*net_wall),
        roof_area_m2=_rv(*roof),
        window_area_m2=_rv(*window),
        heated_volume_m3=_rv(*volume),
        confidence=confidence,
    )


def _vision(
    wall_finish: str = "plaster",
    wall_structure: str = "brick",
    roof_covering: str = "ceramic_tile",
    roof_type: str = "gable",
    window_type: str = "double_glazed",
    insulation: str = "uncertain",
    confidence: float = 0.80,
    needs_more: bool = False,
    cracks: str = "no",
) -> VisionInput:
    return VisionInput(
        wall_finish_material=wall_finish,
        wall_structure_guess=wall_structure,
        roof_covering_material=roof_covering,
        roof_type=roof_type,
        window_type_guess=window_type,
        visible_insulation_signs=insulation,
        condition_flags=ConditionFlagsInput(
            cracks_visible=cracks,
            moisture_stains_visible="no",
            facade_degradation_visible="no",
            roof_damage_visible="no",
            thermal_bridge_risk_visible="no",
        ),
        overall_confidence=confidence,
        needs_more_images=needs_more,
    )


def _request(
    building_type: str = "house",
    vision: VisionInput | None = None,
    geometry: GeometryInput | None = None,
    indoor: float = 20.0,
    outdoor: float = -10.0,
    ach_override: AirtightnessAssumption | None = None,
) -> HeatLossRequest:
    return HeatLossRequest(
        building_id="bld-test",
        building_type=building_type,  # type: ignore[arg-type]
        vision_result=vision or _vision(),
        geometry_result=geometry or _geometry(),
        temperature_scenario=TemperatureScenario(
            indoor_temp_c=indoor, outdoor_temp_c=outdoor
        ),
        airtightness_override=ach_override,
    )


# ---------------------------------------------------------------------------
# Basic calculation
# ---------------------------------------------------------------------------


class TestBasicCalculation:
    def test_returns_heat_loss_response(self) -> None:
        resp = calculate(_request())
        assert isinstance(resp, HeatLossResponse)
        assert resp.building_id == "bld-test"

    def test_four_components_returned(self) -> None:
        resp = calculate(_request())
        components = {c.component for c in resp.component_losses}
        assert components == {"walls", "roof", "windows", "infiltration"}

    def test_all_loss_values_positive(self) -> None:
        resp = calculate(_request())
        for c in resp.component_losses:
            assert c.q_loss_w_low >= 0
            assert c.q_loss_w_base >= 0
            assert c.q_loss_w_high >= 0

    def test_low_le_base_le_high_for_each_component(self) -> None:
        resp = calculate(_request())
        for c in resp.component_losses:
            assert c.q_loss_w_low <= c.q_loss_w_base <= c.q_loss_w_high, (
                f"Range out of order for {c.component}: "
                f"{c.q_loss_w_low} / {c.q_loss_w_base} / {c.q_loss_w_high}"
            )

    def test_summary_transmission_equals_sum_of_components(self) -> None:
        resp = calculate(_request())
        walls, roof, windows = [
            c for c in resp.component_losses if c.component != "infiltration"
        ]
        infiltration = next(c for c in resp.component_losses if c.component == "infiltration")
        s = resp.summary
        assert abs(
            s.transmission_loss_w_base
            - (walls.q_loss_w_base + roof.q_loss_w_base + windows.q_loss_w_base)
        ) < 0.5

    def test_total_equals_transmission_plus_infiltration(self) -> None:
        resp = calculate(_request())
        s = resp.summary
        assert abs(s.total_loss_w_base - (s.transmission_loss_w_base + s.infiltration_loss_w_base)) < 0.5
        assert abs(s.total_loss_w_low - (s.transmission_loss_w_low + s.infiltration_loss_w_low)) < 0.5
        assert abs(s.total_loss_w_high - (s.transmission_loss_w_high + s.infiltration_loss_w_high)) < 0.5

    def test_summary_ranges_ordered(self) -> None:
        resp = calculate(_request())
        s = resp.summary
        assert s.total_loss_w_low <= s.total_loss_w_base <= s.total_loss_w_high

    def test_disclaimers_always_present(self) -> None:
        resp = calculate(_request())
        assert len(resp.disclaimers) >= 4

    def test_delta_t_in_summary(self) -> None:
        resp = calculate(_request(indoor=20.0, outdoor=-10.0))
        assert abs(resp.summary.delta_t_c - 30.0) < 0.01


# ---------------------------------------------------------------------------
# Window type affects result
# ---------------------------------------------------------------------------


class TestWindowTypes:
    @pytest.mark.parametrize("wtype", ["single_glazed", "double_glazed", "triple_glazed"])
    def test_all_window_types_produce_positive_loss(self, wtype: str) -> None:
        resp = calculate(_request(vision=_vision(window_type=wtype)))
        w = next(c for c in resp.component_losses if c.component == "windows")
        assert w.q_loss_w_base > 0

    def test_single_glazed_higher_than_triple(self) -> None:
        single = calculate(_request(vision=_vision(window_type="single_glazed")))
        triple = calculate(_request(vision=_vision(window_type="triple_glazed")))
        w_single = next(c for c in single.component_losses if c.component == "windows")
        w_triple = next(c for c in triple.component_losses if c.component == "windows")
        assert w_single.q_loss_w_base > w_triple.q_loss_w_base

    def test_unknown_window_wider_range_than_known(self) -> None:
        unknown = calculate(_request(vision=_vision(window_type="unknown")))
        known = calculate(_request(vision=_vision(window_type="double_glazed")))
        w_u = next(c for c in unknown.component_losses if c.component == "windows")
        w_k = next(c for c in known.component_losses if c.component == "windows")
        spread_u = w_u.q_loss_w_high - w_u.q_loss_w_low
        spread_k = w_k.q_loss_w_high - w_k.q_loss_w_low
        assert spread_u > spread_k


# ---------------------------------------------------------------------------
# ACH override
# ---------------------------------------------------------------------------


class TestAchOverride:
    def test_override_is_applied(self) -> None:
        override = AirtightnessAssumption(
            ach_low=0.1, ach_base=0.1, ach_high=0.1, source="test override"
        )
        resp = calculate(_request(ach_override=override))
        inf = next(c for c in resp.component_losses if c.component == "infiltration")
        # With ACH=0.1 and volume base=400 and ΔT=30: Q = 0.33*0.1*400*30 = 396 W
        assert abs(inf.q_loss_w_base - 396.0) < 2.0

    def test_override_produces_identical_low_base_high_when_flat(self) -> None:
        override = AirtightnessAssumption(
            ach_low=0.5, ach_base=0.5, ach_high=0.5, source="flat override"
        )
        resp = calculate(_request(ach_override=override, geometry=_geometry(volume=(400.0, 400.0, 400.0))))
        inf = next(c for c in resp.component_losses if c.component == "infiltration")
        assert inf.q_loss_w_low == inf.q_loss_w_base == inf.q_loss_w_high


# ---------------------------------------------------------------------------
# Unknown materials → wider ranges
# ---------------------------------------------------------------------------


class TestUnknownMaterials:
    def test_unknown_wall_structure_produces_wider_wall_range(self) -> None:
        unknown = calculate(_request(vision=_vision(wall_structure="unknown")))
        known = calculate(_request(vision=_vision(wall_structure="brick")))
        uw = next(c for c in unknown.component_losses if c.component == "walls")
        kw = next(c for c in known.component_losses if c.component == "walls")
        assert (uw.q_loss_w_high - uw.q_loss_w_low) > (kw.q_loss_w_high - kw.q_loss_w_low)

    def test_unknown_roof_covering_adds_warning(self) -> None:
        resp = calculate(
            _request(vision=_vision(roof_type="unknown", roof_covering="unknown"))
        )
        assert any("roof type unknown" in w.lower() for w in resp.warnings)

    def test_unknown_wall_structure_adds_warning(self) -> None:
        resp = calculate(_request(vision=_vision(wall_structure="unknown")))
        assert any("wall structure unknown" in w.lower() for w in resp.warnings)


# ---------------------------------------------------------------------------
# Low vision confidence
# ---------------------------------------------------------------------------


class TestLowVisionConfidence:
    def test_low_confidence_adds_warning(self) -> None:
        resp = calculate(_request(vision=_vision(confidence=0.40)))
        assert any("confidence" in w.lower() for w in resp.warnings)

    def test_high_confidence_no_confidence_warning(self) -> None:
        resp = calculate(_request(vision=_vision(confidence=0.90, needs_more=False)))
        assert not any(
            "vision confidence is low" in w.lower() for w in resp.warnings
        )


# ---------------------------------------------------------------------------
# Insulation signs shift U-values
# ---------------------------------------------------------------------------


class TestInsulationSigns:
    def test_visible_insulation_lowers_wall_heat_loss(self) -> None:
        with_ins = calculate(_request(vision=_vision(insulation="yes")))
        without_ins = calculate(_request(vision=_vision(insulation="no")))
        w_with = next(c for c in with_ins.component_losses if c.component == "walls")
        w_without = next(c for c in without_ins.component_losses if c.component == "walls")
        assert w_with.q_loss_w_base < w_without.q_loss_w_base

    def test_sandwich_panel_has_low_wall_loss(self) -> None:
        sandwich = calculate(_request(vision=_vision(wall_finish="sandwich_panel")))
        brick = calculate(_request(vision=_vision(wall_finish="plaster", wall_structure="brick")))
        w_s = next(c for c in sandwich.component_losses if c.component == "walls")
        w_b = next(c for c in brick.component_losses if c.component == "walls")
        assert w_s.q_loss_w_base < w_b.q_loss_w_base


# ---------------------------------------------------------------------------
# Zero heating load (ΔT ≤ 0)
# ---------------------------------------------------------------------------


class TestZeroDeltaT:
    def test_no_heating_load_when_outdoor_equals_indoor(self) -> None:
        resp = calculate(_request(indoor=20.0, outdoor=20.0))
        assert resp.summary.total_loss_w_base == 0.0

    def test_no_heating_load_when_outdoor_warmer(self) -> None:
        resp = calculate(_request(indoor=20.0, outdoor=25.0))
        assert resp.summary.total_loss_w_base == 0.0

    def test_zero_delta_adds_warning(self) -> None:
        resp = calculate(_request(indoor=20.0, outdoor=20.0))
        assert any("no heating load" in w.lower() for w in resp.warnings)


# ---------------------------------------------------------------------------
# Spot-check numerical correctness
# ---------------------------------------------------------------------------


class TestNumericalCorrectness:
    def test_wall_transmission_manual(self) -> None:
        """
        U_base=1.6 W/m²K, A_base=150 m², ΔT=30 K → Q = 1.6*150*30 = 7200 W
        """
        resp = calculate(
            _request(
                vision=_vision(wall_structure="brick"),  # U_base=1.6
                geometry=_geometry(net_wall=(150.0, 150.0, 150.0)),
                indoor=20.0,
                outdoor=-10.0,
            )
        )
        walls = next(c for c in resp.component_losses if c.component == "walls")
        assert abs(walls.q_loss_w_base - 7200.0) < 50.0

    def test_infiltration_manual(self) -> None:
        """
        Q = 0.33 * ACH_base * V_base * ΔT
        House default ACH_base = 0.70, V = 400 m³, ΔT = 30 K
        Q = 0.33 * 0.70 * 400 * 30 = 2772 W
        """
        resp = calculate(
            _request(
                geometry=_geometry(volume=(400.0, 400.0, 400.0)),
                indoor=20.0,
                outdoor=-10.0,
            )
        )
        inf = next(c for c in resp.component_losses if c.component == "infiltration")
        assert abs(inf.q_loss_w_base - 2772.0) < 50.0

    def test_geometry_confidence_warning(self) -> None:
        resp = calculate(_request(geometry=_geometry(confidence=0.40)))
        assert any("geometry confidence" in w.lower() for w in resp.warnings)
