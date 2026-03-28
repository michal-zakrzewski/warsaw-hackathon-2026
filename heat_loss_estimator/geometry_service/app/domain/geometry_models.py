from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

BuildingType = Literal[
    "house",
    "apartment_block",
    "office",
    "warehouse",
    "industrial",
    "unknown",
]


# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------


class BuildingDimensionsHint(BaseModel):
    """User-supplied dimensional data.  All fields are optional — the more
    are provided, the narrower the resulting uncertainty ranges."""

    footprint_area_m2: float | None = Field(default=None, gt=0)
    building_length_m: float | None = Field(default=None, gt=0)
    building_width_m: float | None = Field(default=None, gt=0)
    floors_count: int | None = Field(default=None, ge=1)
    floor_height_m: float | None = Field(default=None, gt=0)
    window_to_wall_ratio_hint: float | None = Field(default=None, ge=0.0, le=1.0)
    roof_slope_deg: float | None = Field(default=None, ge=0.0, le=90.0)
    ceiling_height_m: float | None = Field(default=None, gt=0)
    heated_volume_m3_hint: float | None = Field(default=None, gt=0)


class VisionResultInput(BaseModel):
    """Subset of AggregatedVisionResult fields consumed by geometry service.

    Accepts the full AggregatedVisionResult JSON (extra fields are ignored)
    or a minimal dict with only the relevant keys.
    """

    model_config = ConfigDict(extra="ignore")

    roof_type: str = "unknown"
    window_type_guess: str = "unknown"
    overall_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    needs_more_images: bool = True


class GeometryRequest(BaseModel):
    building_id: str
    building_type: BuildingType
    vision_result: VisionResultInput
    dimensions_hint: BuildingDimensionsHint
    user_notes: str | None = None


# ---------------------------------------------------------------------------
# Output models
# ---------------------------------------------------------------------------


class RangeValue(BaseModel):
    """A quantity expressed as low / base / high estimate."""

    low: float
    base: float
    high: float
    unit: str


class GeometryAssumptions(BaseModel):
    """Records every value that was assumed rather than measured."""

    assumed_floors_count: int
    assumed_floor_height_m: RangeValue
    assumed_window_to_wall_ratio: RangeValue
    assumed_roof_slope_deg: RangeValue
    assumption_notes: list[str]


class GeometryEstimate(BaseModel):
    footprint_area_m2: RangeValue
    perimeter_m: RangeValue
    facade_height_m: RangeValue
    gross_wall_area_m2: RangeValue
    window_area_m2: RangeValue
    net_wall_area_m2: RangeValue
    roof_area_m2: RangeValue
    heated_volume_m3: RangeValue
    confidence: float = Field(ge=0.0, le=1.0)
    warnings: list[str]
    assumptions: GeometryAssumptions


class GeometryResponse(BaseModel):
    building_id: str
    estimate: GeometryEstimate
