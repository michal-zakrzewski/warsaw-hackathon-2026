from __future__ import annotations

from app.domain.geometry_models import (
    BuildingDimensionsHint,
    GeometryAssumptions,
    GeometryEstimate,
    GeometryRequest,
    GeometryResponse,
    RangeValue,
    VisionResultInput,
)
from app.services.geometry_heuristics import (
    PROFILES,
    BuildingProfile,
    compute_confidence,
    mul_ranges,
    range_rel,
    resolve_facade_height,
    resolve_floor_height,
    resolve_footprint,
    resolve_perimeter,
    resolve_roof_area,
    resolve_roof_slope_deg,
    resolve_wwr,
    sub_ranges,
)


def estimate_geometry(request: GeometryRequest) -> GeometryResponse:
    hint = request.dimensions_hint
    vision = request.vision_result
    btype = request.building_type
    profile = PROFILES[btype]

    warnings: list[str] = []
    assumption_notes: list[str] = []

    # --- Floors ---
    floors_count, floors_assumed = _resolve_floors(hint, profile, btype, warnings, assumption_notes)

    # --- Floor height ---
    floor_height, floor_height_assumed = resolve_floor_height(
        hint.floor_height_m, hint.ceiling_height_m, profile
    )
    if floor_height_assumed:
        assumption_notes.append(
            f"Floor height assumed {floor_height.base} m (range {floor_height.low}–{floor_height.high} m)"
            f" based on building type '{btype}'"
        )

    # --- Footprint ---
    footprint, footprint_source = resolve_footprint(
        hint.footprint_area_m2,
        hint.building_length_m,
        hint.building_width_m,
        hint.heated_volume_m3_hint,
        floor_height.base,
        floors_count,
        profile,
    )
    if footprint_source.startswith("estimated"):
        warnings.append(
            "No footprint or dimensions provided — footprint estimated from building type defaults"
        )
        assumption_notes.append(
            f"Footprint assumed {footprint.base} m² (range {footprint.low}–{footprint.high} m²)"
        )

    # --- Perimeter ---
    perimeter, perimeter_source = resolve_perimeter(
        hint.building_length_m, hint.building_width_m, footprint, profile
    )
    if "rectangular shape assumption" in perimeter_source:
        assumption_notes.append(
            f"Perimeter derived from footprint assuming rectangular plan "
            f"with L/W ≈ {profile.shape_factor}"
        )

    # --- Facade height ---
    facade_height = resolve_facade_height(floors_count, floors_assumed, floor_height)

    # --- WWR ---
    wwr = resolve_wwr(hint.window_to_wall_ratio_hint, profile)
    if hint.window_to_wall_ratio_hint is None:
        assumption_notes.append(
            f"Window-to-wall ratio assumed {wwr.base:.0%} (range {wwr.low:.0%}–{wwr.high:.0%})"
            f" based on building type '{btype}'"
        )
        if vision.window_type_guess not in ("unknown", "uncertain"):
            assumption_notes.append(
                f"Vision detected window glazing type '{vision.window_type_guess}' — "
                "this reflects glazing quality, not coverage fraction, so WWR was not adjusted"
            )

    # --- Wall areas ---
    gross_wall = mul_ranges(perimeter, facade_height, "m²")
    window_area = _wwr_to_area(gross_wall, wwr)
    net_wall = sub_ranges(gross_wall, window_area)

    # --- Roof ---
    roof_type = vision.roof_type
    slope_deg, slope_assumed = resolve_roof_slope_deg(hint.roof_slope_deg, roof_type)
    roof_area = resolve_roof_area(footprint, roof_type)

    if roof_type == "unknown":
        warnings.append(
            "Roof type unknown — roof area uses wide uncertainty range (1.0×–1.4× footprint)"
        )
    if roof_type in ("mansard", "sawtooth"):
        warnings.append(
            f"Roof type '{roof_type}' has complex geometry; roof area estimate is approximate"
        )
    if slope_assumed:
        assumption_notes.append(
            f"Roof slope assumed {slope_deg.base}° (default for '{roof_type}' roof type)"
        )

    # --- Heated volume ---
    if hint.heated_volume_m3_hint is not None:
        heated_volume = range_rel(hint.heated_volume_m3_hint, 0.05, "m³")
    else:
        heated_volume = mul_ranges(footprint, facade_height, "m³")

    # --- Quality gates ---
    _add_quality_warnings(hint, vision, btype, warnings)

    # --- Confidence ---
    confidence = compute_confidence(
        has_length_width=(
            hint.building_length_m is not None and hint.building_width_m is not None
        ),
        has_footprint=hint.footprint_area_m2 is not None,
        has_floors=hint.floors_count is not None,
        has_floor_height=(
            hint.floor_height_m is not None or hint.ceiling_height_m is not None
        ),
        roof_type_known=roof_type != "unknown",
        vision_confidence=vision.overall_confidence,
    )

    assumptions = GeometryAssumptions(
        assumed_floors_count=floors_count,
        assumed_floor_height_m=floor_height,
        assumed_window_to_wall_ratio=wwr,
        assumed_roof_slope_deg=slope_deg,
        assumption_notes=assumption_notes,
    )

    estimate = GeometryEstimate(
        footprint_area_m2=footprint,
        perimeter_m=perimeter,
        facade_height_m=facade_height,
        gross_wall_area_m2=gross_wall,
        window_area_m2=window_area,
        net_wall_area_m2=net_wall,
        roof_area_m2=roof_area,
        heated_volume_m3=heated_volume,
        confidence=confidence,
        warnings=warnings,
        assumptions=assumptions,
    )

    return GeometryResponse(building_id=request.building_id, estimate=estimate)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _resolve_floors(
    hint: BuildingDimensionsHint,
    profile: BuildingProfile,
    btype: str,
    warnings: list[str],
    assumption_notes: list[str],
) -> tuple[int, bool]:
    if hint.floors_count is not None:
        return hint.floors_count, False

    floors = profile.floors_count
    warnings.append(
        f"Floors count not provided — assumed {floors} floors based on building type '{btype}'"
    )
    assumption_notes.append(
        f"Floors count assumed {floors} (typical for '{btype}')"
    )
    return floors, True


def _wwr_to_area(gross_wall: RangeValue, wwr: RangeValue) -> RangeValue:
    """Window area = gross_wall × WWR, propagated as independent ranges."""
    return RangeValue(
        low=round(gross_wall.low * wwr.low, 2),
        base=round(gross_wall.base * wwr.base, 2),
        high=round(gross_wall.high * wwr.high, 2),
        unit="m²",
    )


def _add_quality_warnings(
    hint: BuildingDimensionsHint,
    vision: VisionResultInput,
    btype: str,
    warnings: list[str],
) -> None:
    if vision.overall_confidence < 0.50:
        warnings.append(
            f"Vision service confidence is low ({vision.overall_confidence:.0%}) — "
            "roof type and material assumptions may be unreliable"
        )
    if vision.needs_more_images:
        warnings.append(
            "Vision service flagged that more building images are needed for reliable assessment"
        )
    if btype == "unknown":
        warnings.append(
            "Building type is unknown — all defaults are very approximate"
        )
