"""Deterministic building heat-loss estimation tools for the ADK agent.

All physics is self-contained — no dependency on the heat_loss_estimator
FastAPI service directories.  Gemini handles the visual analysis; these
functions do the deterministic geometry and thermodynamics math.

Formula summary
---------------
Transmission  : Q = U · A · ΔT          [W]
Infiltration  : Q = 0.33 · ACH · V · ΔT  [W]

Results are low / base / high ranges.  Provide more dimensions or clearer
images to narrow the range.

Sources: EN ISO 6946, EN 12831-1, TABULA Polish building stock data.
"""

from __future__ import annotations

import math
from typing import Any

# ---------------------------------------------------------------------------
# Building-type profiles (geometry + airtightness defaults)
# ---------------------------------------------------------------------------

_PROFILES: dict[str, dict[str, Any]] = {
    "house": dict(
        floors=2, floor_h=2.70, floor_h_low=2.40, floor_h_high=3.00,
        wwr=0.18, wwr_low=0.11, wwr_high=0.25,
        footprint=100.0, shape_factor=1.4,
        ach_low=0.30, ach_base=0.70, ach_high=1.50,
    ),
    "apartment_block": dict(
        floors=5, floor_h=2.80, floor_h_low=2.60, floor_h_high=3.00,
        wwr=0.25, wwr_low=0.17, wwr_high=0.33,
        footprint=500.0, shape_factor=2.0,
        ach_low=0.20, ach_base=0.50, ach_high=1.00,
    ),
    "office": dict(
        floors=4, floor_h=3.20, floor_h_low=2.80, floor_h_high=3.60,
        wwr=0.35, wwr_low=0.23, wwr_high=0.47,
        footprint=800.0, shape_factor=1.5,
        ach_low=0.30, ach_base=0.60, ach_high=1.20,
    ),
    "warehouse": dict(
        floors=1, floor_h=6.00, floor_h_low=4.00, floor_h_high=8.00,
        wwr=0.05, wwr_low=0.02, wwr_high=0.08,
        footprint=2000.0, shape_factor=2.0,
        ach_low=0.50, ach_base=1.00, ach_high=2.50,
    ),
    "industrial": dict(
        floors=1, floor_h=7.00, floor_h_low=4.00, floor_h_high=10.00,
        wwr=0.08, wwr_low=0.03, wwr_high=0.13,
        footprint=3000.0, shape_factor=1.8,
        ach_low=0.50, ach_base=1.20, ach_high=3.00,
    ),
    "unknown": dict(
        floors=2, floor_h=2.80, floor_h_low=2.20, floor_h_high=3.60,
        wwr=0.20, wwr_low=0.08, wwr_high=0.40,
        footprint=150.0, shape_factor=1.5,
        ach_low=0.30, ach_base=0.80, ach_high=2.00,
    ),
}

# ---------------------------------------------------------------------------
# U-value tables  (W/m²K): (low, base, high)
# ---------------------------------------------------------------------------

# Wall: primary key = wall_structure_guess
_WALL_U: dict[str, tuple[float, float, float]] = {
    "brick":        (0.80, 1.60, 2.50),   # solid/cavity, era unknown
    "concrete":     (0.80, 1.40, 2.20),   # precast or cast-in-place
    "aac":          (0.25, 0.50, 0.90),   # autoclaved aerated concrete
    "timber_frame": (0.20, 0.45, 1.00),   # insulation level unknown
    "steel_frame":  (0.40, 1.00, 2.50),   # depends heavily on envelope
    "mixed":        (0.50, 1.20, 2.50),
    "unknown":      (0.50, 1.50, 3.00),
}

# Wall: finish-based overrides (take priority over structure key)
_WALL_U_FINISH_OVERRIDE: dict[str, tuple[float, float, float]] = {
    "sandwich_panel": (0.15, 0.30, 0.50),
    "glass_curtain":  (1.00, 2.00, 3.50),
}

# Roof: primary key = roof_covering_material
_ROOF_U: dict[str, tuple[float, float, float]] = {
    "metal_sheet":       (0.30, 1.20, 3.50),
    "ceramic_tile":      (0.15, 0.45, 1.00),
    "concrete_tile":     (0.15, 0.45, 1.00),
    "bitumen_membrane":  (0.15, 0.50, 1.20),
    "shingle":           (0.20, 0.55, 1.20),
    "green_roof":        (0.10, 0.20, 0.40),
    "unknown":           (0.20, 0.80, 2.50),
}

# Window: primary key = window_type_guess
_WINDOW_U: dict[str, tuple[float, float, float]] = {
    "single_glazed":  (4.0, 5.0, 6.0),
    "double_glazed":  (1.0, 2.0, 3.0),
    "triple_glazed":  (0.5, 0.8, 1.2),
    "mixed":          (1.5, 3.0, 5.0),
    "unknown":        (1.0, 3.0, 6.0),
}

# Roof area = footprint × factor; (low, base, high) multipliers
_ROOF_FACTOR: dict[str, tuple[float, float, float]] = {
    "flat":     (1.00, 1.00, 1.05),
    "gable":    (1.10, 1.15, 1.25),
    "hip":      (1.10, 1.15, 1.25),
    "shed":     (1.05, 1.10, 1.18),
    "mansard":  (1.20, 1.35, 1.55),
    "sawtooth": (1.20, 1.30, 1.50),
    "unknown":  (1.00, 1.15, 1.40),
}

# U-value multipliers for (u_low, u_base, u_high) based on visible insulation
_INSULATION_MULT: dict[str, tuple[float, float, float]] = {
    "yes":       (0.90, 0.60, 0.70),   # visible EWI → lower U
    "no":        (1.00, 1.10, 1.30),   # no external insulation seen
    "uncertain": (1.00, 1.00, 1.00),
}

_AIR_FACTOR = 0.33  # W/(m³·K·h⁻¹)  from ρ·cₚ/3600

_DISCLAIMERS = [
    "This is a pre-estimate only — not a certified energy audit.",
    "Results rely on visual assessment and heuristic defaults; on-site measurements will differ.",
    "Standard photographs cannot reveal hidden insulation, thermal bridges, or airtightness defects.",
    "Thermographic surveys and blower-door testing are recommended for reliable assessment.",
]

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _p(building_type: str) -> dict[str, Any]:
    return _PROFILES.get(building_type, _PROFILES["unknown"])


def _r(x: float) -> float:
    return round(max(0.0, x), 1)


def _rv(low: float, base: float, high: float) -> dict[str, float]:
    return {"low": _r(low), "base": _r(base), "high": _r(high)}


def _wall_u(
    wall_finish: str, wall_structure: str, visible_insulation: str
) -> tuple[float, float, float]:
    base = _WALL_U_FINISH_OVERRIDE.get(wall_finish) or _WALL_U.get(
        wall_structure, _WALL_U["unknown"]
    )
    # Sandwich panels already encode insulation; skip multiplier.
    mult = (
        (1.0, 1.0, 1.0)
        if wall_finish == "sandwich_panel"
        else _INSULATION_MULT.get(visible_insulation, (1.0, 1.0, 1.0))
    )
    return (
        round(base[0] * mult[0], 3),
        round(base[1] * mult[1], 3),
        round(base[2] * mult[2], 3),
    )


def _roof_u(
    roof_covering: str, visible_insulation: str
) -> tuple[float, float, float]:
    base = _ROOF_U.get(roof_covering, _ROOF_U["unknown"])
    mult = _INSULATION_MULT.get(visible_insulation, (1.0, 1.0, 1.0))
    return (
        round(base[0] * mult[0], 3),
        round(base[1] * mult[1], 3),
        round(base[2] * mult[2], 3),
    )


def _ach(
    building_type: str, cracks: str, facade_degradation: str, visible_insulation: str
) -> tuple[float, float, float]:
    prof = _p(building_type)
    al, ab, ah = prof["ach_low"], prof["ach_base"], prof["ach_high"]

    if cracks == "yes":
        ab *= 1.40; ah *= 1.60
    elif cracks == "uncertain":
        ah *= 1.20

    if facade_degradation == "yes":
        ab *= 1.25; ah *= 1.35

    if visible_insulation == "yes":
        al *= 0.75; ab *= 0.75
    elif visible_insulation == "no":
        ab *= 1.10; ah *= 1.20

    return round(al, 3), round(ab, 3), round(ah, 3)


def _resolve_geometry(
    building_type: str,
    roof_type: str,
    footprint_area_m2: float | None,
    building_length_m: float | None,
    building_width_m: float | None,
    floors_count: int | None,
    floor_height_m: float | None,
    window_to_wall_ratio_hint: float | None,
    warnings: list[str],
) -> dict[str, Any]:
    prof = _p(building_type)

    # --- Footprint & perimeter ---
    if building_length_m and building_width_m:
        fp_base = building_length_m * building_width_m
        fp_unc = 0.03
        pr_base = 2.0 * (building_length_m + building_width_m)
        pr_unc = 0.04
    elif footprint_area_m2:
        fp_base = footprint_area_m2
        fp_unc = 0.05
        sf = prof["shape_factor"]
        w = math.sqrt(fp_base / sf)
        pr_base = 2.0 * (sf * w + w)
        pr_unc = 0.20
    else:
        fp_base = prof["footprint"]
        fp_unc = 0.40
        sf = prof["shape_factor"]
        w = math.sqrt(fp_base / sf)
        pr_base = 2.0 * (sf * w + w)
        pr_unc = 0.40
        warnings.append(
            f"No dimensions provided — footprint estimated from '{building_type}' defaults"
        )

    fp_low, fp_high = fp_base * (1 - fp_unc), fp_base * (1 + fp_unc)
    pr_low, pr_high = pr_base * (1 - pr_unc), pr_base * (1 + pr_unc)

    # --- Floor height ---
    if floor_height_m:
        fh_low = fh_base = fh_high = floor_height_m
    else:
        fh_base = prof["floor_h"]
        fh_low = prof["floor_h_low"]
        fh_high = prof["floor_h_high"]

    # --- Floors ---
    assumed_floors = floors_count is None
    n = floors_count or prof["floors"]
    if assumed_floors:
        warnings.append(
            f"Floors count not provided — assumed {n} floors for '{building_type}'"
        )

    # --- Facade height ---
    fac_low = max(1, n - 1 if assumed_floors else n) * fh_low
    fac_base = n * fh_base
    fac_high = (n + 1 if assumed_floors else n) * fh_high

    # --- WWR ---
    if window_to_wall_ratio_hint is not None:
        wwr_low = wwr_base = wwr_high = window_to_wall_ratio_hint
    else:
        wwr_base = prof["wwr"]
        wwr_low = prof["wwr_low"]
        wwr_high = prof["wwr_high"]

    # --- Wall areas ---
    gw_low, gw_base, gw_high = pr_low * fac_low, pr_base * fac_base, pr_high * fac_high
    win_low = gw_low * wwr_low
    win_base = gw_base * wwr_base
    win_high = gw_high * wwr_high
    net_low = max(0.0, gw_low - win_high)
    net_base = max(0.0, gw_base - win_base)
    net_high = max(0.0, gw_high - win_low)

    # --- Roof ---
    rf = _ROOF_FACTOR.get(roof_type, _ROOF_FACTOR["unknown"])
    roof_low, roof_base, roof_high = fp_low * rf[0], fp_base * rf[1], fp_high * rf[2]

    # --- Volume ---
    vol_low = fp_low * fac_low
    vol_base = fp_base * fac_base
    vol_high = fp_high * fac_high

    # --- Confidence ---
    conf = 1.0
    if not (building_length_m and building_width_m):
        conf *= 0.90 if footprint_area_m2 else 0.55
    if assumed_floors:
        conf *= 0.80
    if not floor_height_m:
        conf *= 0.85

    return {
        "footprint_m2":      _rv(fp_low, fp_base, fp_high),
        "net_wall_area_m2":  _rv(net_low, net_base, net_high),
        "roof_area_m2":      _rv(roof_low, roof_base, roof_high),
        "window_area_m2":    _rv(win_low, win_base, win_high),
        "heated_volume_m3":  _rv(vol_low, vol_base, vol_high),
        "geometry_confidence": round(conf, 3),
    }


# ---------------------------------------------------------------------------
# Public ADK tools
# ---------------------------------------------------------------------------


def estimate_building_geometry(
    building_type: str = "house",
    roof_type: str = "unknown",
    footprint_area_m2: float | None = None,
    building_length_m: float | None = None,
    building_width_m: float | None = None,
    floors_count: int | None = None,
    floor_height_m: float | None = None,
    window_to_wall_ratio_hint: float | None = None,
) -> dict:
    """Estimate building envelope areas from visual observations and optional dimensions.

    Use this when the user asks about building size, wall area, roof area, or
    heated volume — without necessarily needing a full heat-loss calculation.
    Provide as many measured dimensions as available for a tighter estimate.

    Args:
        building_type: house | apartment_block | office | warehouse | industrial | unknown
        roof_type: Roof form observed in images: flat | gable | hip | shed | mansard | sawtooth | unknown
        footprint_area_m2: Ground-floor area in m², if known.
        building_length_m: Longer plan dimension in m, if known.
        building_width_m: Shorter plan dimension in m, if known.
        floors_count: Number of above-ground heated floors, if known.
        floor_height_m: Floor-to-floor height in m, if known.
        window_to_wall_ratio_hint: Fraction of facade area covered by windows (0–1), if known.

    Returns:
        Dict with footprint, net wall area, roof area, window area, heated volume
        (each as low/base/high in m² or m³), geometry confidence (0–1), and warnings.
    """
    warnings: list[str] = []
    geom = _resolve_geometry(
        building_type, roof_type, footprint_area_m2,
        building_length_m, building_width_m, floors_count,
        floor_height_m, window_to_wall_ratio_hint, warnings,
    )
    return {**geom, "warnings": warnings}


def estimate_heat_loss(
    building_type: str = "house",
    # --- Visual features (Gemini fills these from image analysis) ---
    wall_finish_material: str = "unknown",
    wall_structure_guess: str = "unknown",
    roof_covering_material: str = "unknown",
    roof_type: str = "unknown",
    window_type_guess: str = "unknown",
    visible_insulation_signs: str = "uncertain",
    cracks_visible: str = "uncertain",
    facade_degradation_visible: str = "uncertain",
    thermal_bridge_risk_visible: str = "uncertain",
    vision_confidence: float = 0.7,
    # --- User-supplied dimensions (all optional) ---
    footprint_area_m2: float | None = None,
    building_length_m: float | None = None,
    building_width_m: float | None = None,
    floors_count: int | None = None,
    floor_height_m: float | None = None,
    window_to_wall_ratio_hint: float | None = None,
    # --- Temperature scenario ---
    indoor_temp_c: float = 20.0,
    outdoor_temp_c: float = -10.0,
) -> dict:
    """Estimate building heat loss from visual observations and optional measured dimensions.

    Call this after analysing building photographs.  Fill in the visual feature
    arguments from what you observe in the images.  Provide measured dimensions
    whenever the user supplies them — each known value narrows the uncertainty range.

    Args:
        building_type: house | apartment_block | office | warehouse | industrial | unknown
        wall_finish_material: Observed exterior finish: plaster | brick_face | concrete | wood |
            siding | sandwich_panel | glass_curtain | metal_cladding | unknown
        wall_structure_guess: Inferred structural system: brick | concrete | aac |
            timber_frame | steel_frame | mixed | unknown
        roof_covering_material: Observed roof surface: metal_sheet | ceramic_tile |
            concrete_tile | bitumen_membrane | shingle | green_roof | unknown
        roof_type: Observed roof form: flat | gable | hip | shed | mansard | sawtooth | unknown
        window_type_guess: Observed glazing type: single_glazed | double_glazed |
            triple_glazed | mixed | unknown
        visible_insulation_signs: External insulation signs visible? yes | no | uncertain
        cracks_visible: Cracks observed in facade? yes | no | uncertain
        facade_degradation_visible: Facade degradation observed? yes | no | uncertain
        thermal_bridge_risk_visible: Thermal bridge risk signs? yes | no | uncertain
        vision_confidence: Your overall confidence in the visual assessment (0–1).
        footprint_area_m2: Ground-floor area in m², if the user provided it.
        building_length_m: Longer plan dimension in m, if known.
        building_width_m: Shorter plan dimension in m, if known.
        floors_count: Number of above-ground heated floors, if known.
        floor_height_m: Floor-to-floor height in m, if known.
        window_to_wall_ratio_hint: Fraction of facade covered by windows (0–1), if known.
        indoor_temp_c: Design indoor temperature °C (default 20).
        outdoor_temp_c: Design outdoor temperature °C (default −10).

    Returns:
        Dict with geometry estimates, selected assemblies, per-component heat losses
        (walls, roof, windows, infiltration), summary (low/base/high in W and kW),
        warnings, and disclaimers.
    """
    warnings: list[str] = []

    delta_t = indoor_temp_c - outdoor_temp_c

    if delta_t <= 0:
        warnings.append(
            f"Outdoor temperature ({outdoor_temp_c}°C) ≥ indoor ({indoor_temp_c}°C) — "
            "no heating demand; all losses returned as 0 W"
        )
        return {
            "summary": {"delta_t_c": round(delta_t, 1),
                        "total_w": {"low": 0.0, "base": 0.0, "high": 0.0},
                        "total_kw": {"low": 0.0, "base": 0.0, "high": 0.0}},
            "warnings": warnings, "disclaimers": _DISCLAIMERS,
        }

    # --- Geometry ---
    geom = _resolve_geometry(
        building_type, roof_type, footprint_area_m2,
        building_length_m, building_width_m, floors_count,
        floor_height_m, window_to_wall_ratio_hint, warnings,
    )

    nw = geom["net_wall_area_m2"]
    ra = geom["roof_area_m2"]
    wa = geom["window_area_m2"]
    vol = geom["heated_volume_m3"]

    # --- U-values ---
    wu = _wall_u(wall_finish_material, wall_structure_guess, visible_insulation_signs)
    ru = _roof_u(roof_covering_material, visible_insulation_signs)
    winu = _WINDOW_U.get(window_type_guess, _WINDOW_U["unknown"])

    # --- ACH ---
    al, ab, ah = _ach(building_type, cracks_visible, facade_degradation_visible, visible_insulation_signs)

    # --- Component losses: Q = U * A * ΔT ---
    walls_w = _rv(wu[0] * nw["low"] * delta_t, wu[1] * nw["base"] * delta_t, wu[2] * nw["high"] * delta_t)
    roof_w  = _rv(ru[0] * ra["low"] * delta_t, ru[1] * ra["base"] * delta_t, ru[2] * ra["high"] * delta_t)
    win_w   = _rv(winu[0] * wa["low"] * delta_t, winu[1] * wa["base"] * delta_t, winu[2] * wa["high"] * delta_t)

    # --- Infiltration: Q = 0.33 * ACH * V * ΔT ---
    inf_w = _rv(
        _AIR_FACTOR * al * vol["low"] * delta_t,
        _AIR_FACTOR * ab * vol["base"] * delta_t,
        _AIR_FACTOR * ah * vol["high"] * delta_t,
    )

    # --- Summary ---
    tr_low  = walls_w["low"]  + roof_w["low"]  + win_w["low"]
    tr_base = walls_w["base"] + roof_w["base"] + win_w["base"]
    tr_high = walls_w["high"] + roof_w["high"] + win_w["high"]

    tot_low  = _r(tr_low  + inf_w["low"])
    tot_base = _r(tr_base + inf_w["base"])
    tot_high = _r(tr_high + inf_w["high"])

    # --- Quality warnings ---
    if vision_confidence < 0.55:
        warnings.append(
            f"Vision confidence is low ({vision_confidence:.0%}) — "
            "material U-value assignments are uncertain"
        )
    if wall_structure_guess == "unknown":
        warnings.append("Wall structure unknown — U-value range spans 0.5–3.0 W/m²K")
    if window_type_guess == "unknown":
        warnings.append("Window type unknown — U-value range spans 1.0–6.0 W/m²K")
    if roof_type == "unknown":
        warnings.append("Roof type unknown — roof area estimate uses wide multiplier (1.0–1.4×)")
    if building_type == "unknown":
        warnings.append("Building type unknown — all geometry and ACH defaults are approximate")
    if thermal_bridge_risk_visible == "yes":
        warnings.append(
            "Thermal bridges visible — actual losses may be higher; "
            "thermal bridges are not explicitly modelled here"
        )
    if geom["geometry_confidence"] < 0.60:
        warnings.append(
            f"Geometry confidence: {geom['geometry_confidence']:.0%} — "
            "supply length, width, and floors for a tighter estimate"
        )

    wall_u_label = f"{wu[0]}–{wu[2]} W/m²K (base {wu[1]})"
    roof_u_label = f"{ru[0]}–{ru[2]} W/m²K (base {ru[1]})"
    win_u_label  = f"{winu[0]}–{winu[2]} W/m²K (base {winu[1]})"
    ach_label    = f"{al}–{ah} h⁻¹ (base {ab})"

    return {
        "geometry": {
            "footprint_m2":      geom["footprint_m2"],
            "net_wall_area_m2":  geom["net_wall_area_m2"],
            "roof_area_m2":      geom["roof_area_m2"],
            "window_area_m2":    geom["window_area_m2"],
            "heated_volume_m3":  geom["heated_volume_m3"],
            "confidence":        geom["geometry_confidence"],
        },
        "selected_assemblies": {
            "wall":   {"description": f"{wall_structure_guess} wall / {wall_finish_material} finish", "u_value": wall_u_label},
            "roof":   {"description": f"{roof_covering_material} roof / {roof_type}", "u_value": roof_u_label},
            "window": {"description": window_type_guess, "u_value": win_u_label},
            "airtightness": {"ach_range": ach_label, "source": f"{building_type} defaults adjusted for observed conditions"},
        },
        "component_losses_w": {
            "walls":        walls_w,
            "roof":         roof_w,
            "windows":      win_w,
            "infiltration": inf_w,
        },
        "summary": {
            "delta_t_c":        round(delta_t, 1),
            "transmission_w":   _rv(tr_low, tr_base, tr_high),
            "infiltration_w":   inf_w,
            "total_w":          _rv(tot_low, tot_base, tot_high),
            "total_kw":         _rv(tot_low / 1000, tot_base / 1000, tot_high / 1000),
        },
        "warnings":    warnings,
        "disclaimers": _DISCLAIMERS,
    }
