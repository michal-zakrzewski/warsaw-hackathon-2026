"""Deterministic heat-loss calculator.

Formula summary
---------------
Transmission  : Q = U · A · ΔT          [W]
Infiltration  : Q = 0.33 · ACH · V · ΔT  [W]

Range strategy (per task spec):
  low  = U_low  · A_low  · ΔT
  base = U_base · A_base · ΔT
  high = U_high · A_high · ΔT

All Q values are clamped to ≥ 0 W (this engine estimates heating load only).
"""

from __future__ import annotations

from app.config.envelope_defaults import AIR_HEAT_CAPACITY_FACTOR, DISCLAIMERS
from app.domain.heat_loss_models import (
    AirtightnessAssumption,
    ComponentHeatLossRange,
    EnvelopeAssemblyCandidate,
    GeometryInput,
    HeatLossRequest,
    HeatLossResponse,
    HeatLossSummary,
    RangeValueInput,
    SelectedEnvelopeModel,
    VisionInput,
)
from app.services.airtightness_mapper import map_airtightness
from app.services.material_mapper import (
    map_roof_assembly,
    map_wall_assembly,
    map_window_assembly,
)

_LOW_CONFIDENCE_THRESHOLD = 0.55
_LOW_GEOMETRY_CONFIDENCE_THRESHOLD = 0.60


def calculate(request: HeatLossRequest) -> HeatLossResponse:
    vision = request.vision_result
    geometry = request.geometry_result
    delta_t = request.temperature_scenario.indoor_temp_c - request.temperature_scenario.outdoor_temp_c

    warnings: list[str] = []

    if delta_t <= 0:
        warnings.append(
            f"Outdoor temperature ({request.temperature_scenario.outdoor_temp_c}°C) ≥ "
            f"indoor temperature ({request.temperature_scenario.indoor_temp_c}°C) — "
            "no heating load; all heat losses returned as 0 W"
        )
        return _zero_response(request, delta_t, warnings)

    wall_assembly = map_wall_assembly(
        vision.wall_finish_material,
        vision.wall_structure_guess,
        vision.visible_insulation_signs,
        vision.overall_confidence,
    )
    roof_assembly = map_roof_assembly(
        vision.roof_covering_material,
        vision.visible_insulation_signs,
        vision.overall_confidence,
    )
    window_assembly = map_window_assembly(
        vision.window_type_guess,
        vision.overall_confidence,
    )
    airtightness = map_airtightness(
        request.building_type,
        vision.visible_insulation_signs,
        vision.condition_flags,
        request.airtightness_override,
    )

    walls_loss = _transmission_range(wall_assembly, geometry.net_wall_area_m2, delta_t, "walls")
    roof_loss = _transmission_range(roof_assembly, geometry.roof_area_m2, delta_t, "roof")
    windows_loss = _transmission_range(window_assembly, geometry.window_area_m2, delta_t, "windows")
    infiltration_loss = _infiltration_range(airtightness, geometry.heated_volume_m3, delta_t)

    summary = _build_summary(delta_t, walls_loss, roof_loss, windows_loss, infiltration_loss)

    warnings.extend(_collect_warnings(vision, geometry, request.building_type))
    warnings.extend(geometry.warnings)

    return HeatLossResponse(
        building_id=request.building_id,
        selected_model=SelectedEnvelopeModel(
            wall_assembly=wall_assembly,
            roof_assembly=roof_assembly,
            window_assembly=window_assembly,
            airtightness=airtightness,
        ),
        component_losses=[walls_loss, roof_loss, windows_loss, infiltration_loss],
        summary=summary,
        warnings=warnings,
        disclaimers=DISCLAIMERS,
    )


# ---------------------------------------------------------------------------
# Component calculators
# ---------------------------------------------------------------------------


def _transmission_range(
    assembly: EnvelopeAssemblyCandidate,
    area: RangeValueInput,
    delta_t: float,
    component: str,
) -> ComponentHeatLossRange:
    return ComponentHeatLossRange(
        component=component,  # type: ignore[arg-type]
        q_loss_w_low=_r(assembly.u_value_low * area.low * delta_t),
        q_loss_w_base=_r(assembly.u_value_base * area.base * delta_t),
        q_loss_w_high=_r(assembly.u_value_high * area.high * delta_t),
        assumptions=[
            f"Assembly: {assembly.name}",
            f"U-value range: {assembly.u_value_low}–{assembly.u_value_high} W/(m²·K)"
            f"  (base {assembly.u_value_base})",
            f"Area range: {area.low}–{area.high} m²  (base {area.base})",
            f"ΔT = {delta_t:.1f} K",
            f"Source: {assembly.source}",
        ],
    )


def _infiltration_range(
    ach: AirtightnessAssumption,
    volume: RangeValueInput,
    delta_t: float,
) -> ComponentHeatLossRange:
    f = AIR_HEAT_CAPACITY_FACTOR
    return ComponentHeatLossRange(
        component="infiltration",
        q_loss_w_low=_r(f * ach.ach_low * volume.low * delta_t),
        q_loss_w_base=_r(f * ach.ach_base * volume.base * delta_t),
        q_loss_w_high=_r(f * ach.ach_high * volume.high * delta_t),
        assumptions=[
            f"Formula: Q = {f} × ACH × V × ΔT",
            f"ACH range: {ach.ach_low}–{ach.ach_high} h⁻¹  (base {ach.ach_base})",
            f"Volume range: {volume.low}–{volume.high} m³  (base {volume.base})",
            f"ΔT = {delta_t:.1f} K",
            f"Source: {ach.source}",
        ],
    )


def _build_summary(
    delta_t: float,
    walls: ComponentHeatLossRange,
    roof: ComponentHeatLossRange,
    windows: ComponentHeatLossRange,
    infiltration: ComponentHeatLossRange,
) -> HeatLossSummary:
    trans_low = walls.q_loss_w_low + roof.q_loss_w_low + windows.q_loss_w_low
    trans_base = walls.q_loss_w_base + roof.q_loss_w_base + windows.q_loss_w_base
    trans_high = walls.q_loss_w_high + roof.q_loss_w_high + windows.q_loss_w_high

    return HeatLossSummary(
        delta_t_c=round(delta_t, 1),
        transmission_loss_w_low=_r(trans_low),
        transmission_loss_w_base=_r(trans_base),
        transmission_loss_w_high=_r(trans_high),
        infiltration_loss_w_low=_r(infiltration.q_loss_w_low),
        infiltration_loss_w_base=_r(infiltration.q_loss_w_base),
        infiltration_loss_w_high=_r(infiltration.q_loss_w_high),
        total_loss_w_low=_r(trans_low + infiltration.q_loss_w_low),
        total_loss_w_base=_r(trans_base + infiltration.q_loss_w_base),
        total_loss_w_high=_r(trans_high + infiltration.q_loss_w_high),
    )


# ---------------------------------------------------------------------------
# Warnings
# ---------------------------------------------------------------------------


def _collect_warnings(
    vision: VisionInput,
    geometry: GeometryInput,
    building_type: str,
) -> list[str]:
    warnings: list[str] = []

    if vision.overall_confidence < _LOW_CONFIDENCE_THRESHOLD:
        warnings.append(
            f"Vision confidence is low ({vision.overall_confidence:.0%}) — "
            "material U-value assignments are highly uncertain"
        )
    if vision.needs_more_images:
        warnings.append(
            "Vision service flagged that more building images are needed; "
            "roof and wall material assignments may be unreliable"
        )
    if vision.roof_type == "unknown":
        warnings.append(
            "Roof type unknown — roof area factor uses wide default range; "
            "actual roof area may differ significantly"
        )
    if vision.wall_structure_guess == "unknown":
        warnings.append(
            "Wall structure unknown — wall U-value range spans all typical "
            "construction types (0.5–3.0 W/m²K)"
        )
    if vision.window_type_guess == "unknown":
        warnings.append(
            "Window type unknown — window U-value range spans single to "
            "triple glazed (1.0–6.0 W/m²K)"
        )
    if building_type == "unknown":
        warnings.append(
            "Building type unknown — airtightness defaults are very approximate"
        )
    if geometry.confidence < _LOW_GEOMETRY_CONFIDENCE_THRESHOLD:
        warnings.append(
            f"Geometry confidence is low ({geometry.confidence:.0%}) — "
            "area estimates have high uncertainty; provide dimensions for better accuracy"
        )
    if vision.condition_flags.thermal_bridge_risk_visible == "yes":
        warnings.append(
            "Thermal bridge risk visible in images — actual heat loss may be higher "
            "than calculated; thermal bridges are not modelled in this estimate"
        )

    return warnings


# ---------------------------------------------------------------------------
# Zero-load response (when ΔT ≤ 0)
# ---------------------------------------------------------------------------


def _zero_response(
    request: HeatLossRequest,
    delta_t: float,
    warnings: list[str],
) -> HeatLossResponse:
    vision = request.vision_result
    zero_component = ComponentHeatLossRange(
        component="walls",
        q_loss_w_low=0.0,
        q_loss_w_base=0.0,
        q_loss_w_high=0.0,
        assumptions=["ΔT ≤ 0 — no heating load"],
    )
    wall_assembly = map_wall_assembly(
        vision.wall_finish_material,
        vision.wall_structure_guess,
        vision.visible_insulation_signs,
        vision.overall_confidence,
    )
    roof_assembly = map_roof_assembly(
        vision.roof_covering_material,
        vision.visible_insulation_signs,
        vision.overall_confidence,
    )
    window_assembly = map_window_assembly(vision.window_type_guess, vision.overall_confidence)
    airtightness = map_airtightness(
        request.building_type,
        vision.visible_insulation_signs,
        vision.condition_flags,
        request.airtightness_override,
    )
    return HeatLossResponse(
        building_id=request.building_id,
        selected_model=SelectedEnvelopeModel(
            wall_assembly=wall_assembly,
            roof_assembly=roof_assembly,
            window_assembly=window_assembly,
            airtightness=airtightness,
        ),
        component_losses=[
            zero_component,
            zero_component.model_copy(update={"component": "roof"}),
            zero_component.model_copy(update={"component": "windows"}),
            zero_component.model_copy(update={"component": "infiltration"}),
        ],
        summary=HeatLossSummary(
            delta_t_c=round(delta_t, 1),
            transmission_loss_w_low=0.0,
            transmission_loss_w_base=0.0,
            transmission_loss_w_high=0.0,
            infiltration_loss_w_low=0.0,
            infiltration_loss_w_base=0.0,
            infiltration_loss_w_high=0.0,
            total_loss_w_low=0.0,
            total_loss_w_base=0.0,
            total_loss_w_high=0.0,
        ),
        warnings=warnings,
        disclaimers=DISCLAIMERS,
    )


def _r(x: float) -> float:
    return round(max(0.0, x), 1)
