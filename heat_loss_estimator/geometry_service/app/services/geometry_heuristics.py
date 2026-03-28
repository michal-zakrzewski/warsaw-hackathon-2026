"""Building geometry heuristics and default profiles.

All "magic numbers" live here so that the service layer stays clean.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from app.domain.geometry_models import RangeValue


# ---------------------------------------------------------------------------
# Building-type profiles
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BuildingProfile:
    """Default geometric parameters for a building type.

    floor_height_low/high define the plausible range when the user does not
    supply a measured value.  wwr_low/high do the same for window-to-wall ratio.
    """

    floors_count: int
    floor_height_base_m: float
    floor_height_low_m: float
    floor_height_high_m: float
    wwr_base: float          # window-to-wall ratio, 0–1
    wwr_low: float
    wwr_high: float
    footprint_typical_m2: float   # fallback when no dimensions given
    shape_factor: float           # L/W ratio for rectangular-footprint assumption


PROFILES: dict[str, BuildingProfile] = {
    "house": BuildingProfile(
        floors_count=2,
        floor_height_base_m=2.70,
        floor_height_low_m=2.40,
        floor_height_high_m=3.00,
        wwr_base=0.18,
        wwr_low=0.11,
        wwr_high=0.25,
        footprint_typical_m2=100.0,
        shape_factor=1.4,
    ),
    "apartment_block": BuildingProfile(
        floors_count=5,
        floor_height_base_m=2.80,
        floor_height_low_m=2.60,
        floor_height_high_m=3.00,
        wwr_base=0.25,
        wwr_low=0.17,
        wwr_high=0.33,
        footprint_typical_m2=500.0,
        shape_factor=2.0,
    ),
    "office": BuildingProfile(
        floors_count=4,
        floor_height_base_m=3.20,
        floor_height_low_m=2.80,
        floor_height_high_m=3.60,
        wwr_base=0.35,
        wwr_low=0.23,
        wwr_high=0.47,
        footprint_typical_m2=800.0,
        shape_factor=1.5,
    ),
    "warehouse": BuildingProfile(
        floors_count=1,
        floor_height_base_m=6.00,
        floor_height_low_m=4.00,
        floor_height_high_m=8.00,
        wwr_base=0.05,
        wwr_low=0.02,
        wwr_high=0.08,
        footprint_typical_m2=2000.0,
        shape_factor=2.0,
    ),
    "industrial": BuildingProfile(
        floors_count=1,
        floor_height_base_m=7.00,
        floor_height_low_m=4.00,
        floor_height_high_m=10.00,
        wwr_base=0.08,
        wwr_low=0.03,
        wwr_high=0.13,
        footprint_typical_m2=3000.0,
        shape_factor=1.8,
    ),
    "unknown": BuildingProfile(
        floors_count=2,
        floor_height_base_m=2.80,
        floor_height_low_m=2.20,
        floor_height_high_m=3.60,
        wwr_base=0.20,
        wwr_low=0.08,
        wwr_high=0.40,
        footprint_typical_m2=150.0,
        shape_factor=1.5,
    ),
}


# ---------------------------------------------------------------------------
# Roof slope factors: footprint × factor → inclined roof area
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RoofFactors:
    default_slope_deg: float
    area_factor_low: float
    area_factor_base: float
    area_factor_high: float


ROOF_FACTORS: dict[str, RoofFactors] = {
    "flat": RoofFactors(
        default_slope_deg=2.0,
        area_factor_low=1.00,
        area_factor_base=1.00,
        area_factor_high=1.05,
    ),
    "gable": RoofFactors(
        default_slope_deg=30.0,
        area_factor_low=1.10,
        area_factor_base=1.15,
        area_factor_high=1.25,
    ),
    "hip": RoofFactors(
        default_slope_deg=30.0,
        area_factor_low=1.10,
        area_factor_base=1.15,
        area_factor_high=1.25,
    ),
    "shed": RoofFactors(
        default_slope_deg=20.0,
        area_factor_low=1.05,
        area_factor_base=1.10,
        area_factor_high=1.18,
    ),
    "mansard": RoofFactors(
        default_slope_deg=45.0,
        area_factor_low=1.20,
        area_factor_base=1.35,
        area_factor_high=1.55,
    ),
    "sawtooth": RoofFactors(
        default_slope_deg=35.0,
        area_factor_low=1.20,
        area_factor_base=1.30,
        area_factor_high=1.50,
    ),
    "unknown": RoofFactors(
        default_slope_deg=25.0,
        area_factor_low=1.00,
        area_factor_base=1.15,
        area_factor_high=1.40,
    ),
}


# ---------------------------------------------------------------------------
# Range arithmetic helpers
# ---------------------------------------------------------------------------


def range_rel(base: float, rel_unc: float, unit: str) -> RangeValue:
    """Symmetric relative uncertainty: base ± rel_unc fraction."""
    return RangeValue(
        low=_r(base * (1.0 - rel_unc)),
        base=_r(base),
        high=_r(base * (1.0 + rel_unc)),
        unit=unit,
    )


def range_explicit(low: float, base: float, high: float, unit: str) -> RangeValue:
    return RangeValue(low=_r(low), base=_r(base), high=_r(high), unit=unit)


def mul_ranges(a: RangeValue, b: RangeValue, unit: str) -> RangeValue:
    """Multiply two independent positive ranges."""
    return RangeValue(
        low=_r(a.low * b.low),
        base=_r(a.base * b.base),
        high=_r(a.high * b.high),
        unit=unit,
    )


def scale_range(r: RangeValue, low_f: float, base_f: float, high_f: float) -> RangeValue:
    """Apply asymmetric scalar factors to each bound."""
    return RangeValue(
        low=_r(r.low * low_f),
        base=_r(r.base * base_f),
        high=_r(r.high * high_f),
        unit=r.unit,
    )


def sub_ranges(a: RangeValue, b: RangeValue) -> RangeValue:
    """Subtract b from a with conservative (widening) propagation.

    net.low = a.low − b.high  (worst case: small a, large b)
    net.high = a.high − b.low (best case: large a, small b)
    """
    return RangeValue(
        low=_r(max(0.0, a.low - b.high)),
        base=_r(max(0.0, a.base - b.base)),
        high=_r(max(0.0, a.high - b.low)),
        unit=a.unit,
    )


# ---------------------------------------------------------------------------
# Footprint + perimeter resolution
# ---------------------------------------------------------------------------


def resolve_footprint(
    footprint_area_m2: float | None,
    length_m: float | None,
    width_m: float | None,
    volume_hint_m3: float | None,
    floor_height_base: float,
    floors_count: int,
    profile: BuildingProfile,
) -> tuple[RangeValue, str]:
    """Return (footprint_range, source_label)."""

    if length_m is not None and width_m is not None:
        base = length_m * width_m
        return range_rel(base, 0.03, "m²"), "user-provided length × width"

    if footprint_area_m2 is not None:
        return range_rel(footprint_area_m2, 0.05, "m²"), "user-provided footprint"

    if volume_hint_m3 is not None:
        total_height = floor_height_base * floors_count
        base = volume_hint_m3 / max(total_height, 1.0)
        return range_rel(base, 0.15, "m²"), "derived from heated-volume hint"

    return range_rel(profile.footprint_typical_m2, 0.40, "m²"), "estimated from building type"


def resolve_perimeter(
    length_m: float | None,
    width_m: float | None,
    footprint: RangeValue,
    profile: BuildingProfile,
) -> tuple[RangeValue, str]:
    """Return (perimeter_range, source_label)."""

    if length_m is not None and width_m is not None:
        base = 2.0 * (length_m + width_m)
        return range_rel(base, 0.04, "m"), "user-provided length × width"

    # Assume rectangular footprint with building-type shape factor (L/W ratio).
    sf = profile.shape_factor
    # footprint = L × W = sf × W²  →  W = sqrt(footprint / sf)
    w_base = math.sqrt(footprint.base / sf)
    w_low = math.sqrt(footprint.low / sf)
    w_high = math.sqrt(footprint.high / sf)
    l_base, l_low, l_high = sf * w_base, sf * w_low, sf * w_high
    base = 2.0 * (l_base + w_base)
    low = 2.0 * (l_low + w_low)
    high = 2.0 * (l_high + w_high)
    # Add extra width uncertainty for shape assumption (actual plan may be L-shaped etc.)
    extra = 0.20
    return range_explicit(
        low * (1.0 - extra),
        base,
        high * (1.0 + extra),
        "m",
    ), "derived from footprint with rectangular shape assumption"


# ---------------------------------------------------------------------------
# Floor height resolution
# ---------------------------------------------------------------------------


def resolve_floor_height(
    floor_height_m: float | None,
    ceiling_height_m: float | None,
    profile: BuildingProfile,
) -> tuple[RangeValue, bool]:
    """Return (floor_height_range, was_assumed).

    ceiling_height → floor height by adding estimated structural slab thickness (0.25 m).
    """
    if floor_height_m is not None:
        return range_rel(floor_height_m, 0.03, "m"), False

    if ceiling_height_m is not None:
        fh = ceiling_height_m + 0.25
        return range_rel(fh, 0.05, "m"), False

    return range_explicit(
        profile.floor_height_low_m,
        profile.floor_height_base_m,
        profile.floor_height_high_m,
        "m",
    ), True


# ---------------------------------------------------------------------------
# Facade height
# ---------------------------------------------------------------------------


def resolve_facade_height(
    floors_count: int,
    floors_assumed: bool,
    floor_height: RangeValue,
) -> RangeValue:
    if floors_assumed:
        floors_low = max(1, floors_count - 1)
        floors_high = floors_count + 1
    else:
        floors_low = floors_high = floors_count

    return range_explicit(
        low=_r(floors_low * floor_height.low),
        base=_r(floors_count * floor_height.base),
        high=_r(floors_high * floor_height.high),
        unit="m",
    )


# ---------------------------------------------------------------------------
# WWR resolution
# ---------------------------------------------------------------------------


def resolve_wwr(
    wwr_hint: float | None,
    profile: BuildingProfile,
) -> RangeValue:
    """Window-to-wall ratio.  Vision's window_type_guess reflects glazing quality,
    not coverage fraction, so it is not used to shift WWR here."""
    if wwr_hint is not None:
        return range_rel(wwr_hint, 0.05, "ratio")

    return range_explicit(profile.wwr_low, profile.wwr_base, profile.wwr_high, "ratio")


# ---------------------------------------------------------------------------
# Roof area
# ---------------------------------------------------------------------------


def resolve_roof_slope_deg(
    slope_hint: float | None,
    roof_type: str,
) -> tuple[RangeValue, bool]:
    """Return (slope_deg_range, was_assumed)."""
    factors = ROOF_FACTORS.get(roof_type, ROOF_FACTORS["unknown"])

    if slope_hint is not None:
        return range_rel(slope_hint, 0.05, "deg"), False

    return range_rel(factors.default_slope_deg, 0.25, "deg"), True


def resolve_roof_area(footprint: RangeValue, roof_type: str) -> RangeValue:
    factors = ROOF_FACTORS.get(roof_type, ROOF_FACTORS["unknown"])
    return scale_range(
        footprint,
        factors.area_factor_low,
        factors.area_factor_base,
        factors.area_factor_high,
    )


# ---------------------------------------------------------------------------
# Confidence score
# ---------------------------------------------------------------------------


def compute_confidence(
    has_length_width: bool,
    has_footprint: bool,
    has_floors: bool,
    has_floor_height: bool,
    roof_type_known: bool,
    vision_confidence: float,
) -> float:
    score = 1.0

    if has_length_width:
        pass  # best case, no penalty
    elif has_footprint:
        score *= 0.90
    else:
        score *= 0.55

    if not has_floors:
        score *= 0.80
    if not has_floor_height:
        score *= 0.85
    if not roof_type_known:
        score *= 0.90

    # Blend 40% with vision confidence (vision tells us about roof type reliability).
    score = score * 0.60 + vision_confidence * 0.40

    return round(min(score, 1.0), 3)


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------


def _r(x: float) -> float:
    return round(x, 2)
