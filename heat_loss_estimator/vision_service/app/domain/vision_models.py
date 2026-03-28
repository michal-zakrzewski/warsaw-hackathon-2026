from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

WallFinishMaterial = Literal[
    "plaster",
    "brick_face",
    "concrete",
    "wood",
    "siding",
    "sandwich_panel",
    "glass_curtain",
    "metal_cladding",
    "unknown",
]

WallStructureGuess = Literal[
    "brick",
    "concrete",
    "aac",
    "timber_frame",
    "steel_frame",
    "mixed",
    "unknown",
]

RoofCoveringMaterial = Literal[
    "metal_sheet",
    "ceramic_tile",
    "concrete_tile",
    "bitumen_membrane",
    "shingle",
    "green_roof",
    "unknown",
]

RoofType = Literal[
    "flat",
    "gable",
    "hip",
    "shed",
    "mansard",
    "sawtooth",
    "unknown",
]

WindowTypeGuess = Literal[
    "single_glazed",
    "double_glazed",
    "triple_glazed",
    "mixed",
    "unknown",
]

Ternary = Literal["yes", "no", "uncertain"]

ViewType = Literal["front", "side", "rear", "roof_oblique", "detail", "unknown"]

BuildingTypeHint = Literal[
    "house",
    "apartment_block",
    "office",
    "warehouse",
    "industrial",
    "unknown",
]


class ImageInput(BaseModel):
    image_id: str
    source_type: Literal["upload", "url"]
    mime_type: str | None = None
    image_url: str | None = None
    storage_path: str | None = None
    view_type: ViewType
    captured_at: datetime | None = None
    notes: str | None = None


class VisionRequest(BaseModel):
    building_id: str
    images: list[ImageInput]
    building_type_hint: BuildingTypeHint = "unknown"
    country_code: str | None = None
    user_notes: str | None = None


class ConditionFlags(BaseModel):
    cracks_visible: Ternary
    moisture_stains_visible: Ternary
    facade_degradation_visible: Ternary
    roof_damage_visible: Ternary
    thermal_bridge_risk_visible: Ternary


class ImageQualityFlags(BaseModel):
    blurry: bool
    low_light: bool
    occluded: bool
    roof_not_visible: bool
    facade_not_visible: bool
    insufficient_detail: bool


class PerImageVisionResult(BaseModel):
    image_id: str
    wall_finish_material: WallFinishMaterial
    wall_structure_guess: WallStructureGuess
    roof_covering_material: RoofCoveringMaterial
    roof_type: RoofType
    window_type_guess: WindowTypeGuess
    visible_insulation_signs: Ternary
    condition_flags: ConditionFlags
    image_quality_flags: ImageQualityFlags
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str]
    missing_information: list[str]


class AggregatedVisionResult(BaseModel):
    wall_finish_material: WallFinishMaterial
    wall_structure_guess: WallStructureGuess
    roof_covering_material: RoofCoveringMaterial
    roof_type: RoofType
    window_type_guess: WindowTypeGuess
    visible_insulation_signs: Ternary
    condition_flags: ConditionFlags
    overall_confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str]
    needs_more_images: bool
    missing_views: list[str]
    quality_warnings: list[str]
    assumption_notes: list[str]


class VisionResponse(BaseModel):
    building_id: str
    per_image_results: list[PerImageVisionResult]
    aggregated: AggregatedVisionResult
