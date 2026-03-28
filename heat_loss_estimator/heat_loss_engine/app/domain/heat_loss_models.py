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
# Upstream-service input adapters
# (accept the full JSON from vision-service / geometry-service; ignore extras)
# ---------------------------------------------------------------------------


class RangeValueInput(BaseModel):
    """Mirrors geometry-service RangeValue.  Unit field is optional."""

    low: float
    base: float
    high: float
    unit: str = ""


class ConditionFlagsInput(BaseModel):
    """Mirrors vision-service ConditionFlags."""

    model_config = ConfigDict(extra="ignore")

    cracks_visible: str = "uncertain"
    moisture_stains_visible: str = "uncertain"
    facade_degradation_visible: str = "uncertain"
    roof_damage_visible: str = "uncertain"
    thermal_bridge_risk_visible: str = "uncertain"


class VisionInput(BaseModel):
    """Subset of AggregatedVisionResult consumed by heat-loss engine.

    Accepts the full AggregatedVisionResult JSON or any compatible dict.
    """

    model_config = ConfigDict(extra="ignore")

    wall_finish_material: str = "unknown"
    wall_structure_guess: str = "unknown"
    roof_covering_material: str = "unknown"
    roof_type: str = "unknown"
    window_type_guess: str = "unknown"
    visible_insulation_signs: str = "uncertain"
    condition_flags: ConditionFlagsInput = Field(default_factory=ConditionFlagsInput)
    overall_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    needs_more_images: bool = True


class GeometryInput(BaseModel):
    """Subset of GeometryEstimate consumed by heat-loss engine."""

    model_config = ConfigDict(extra="ignore")

    net_wall_area_m2: RangeValueInput
    roof_area_m2: RangeValueInput
    window_area_m2: RangeValueInput
    heated_volume_m3: RangeValueInput
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    warnings: list[str] = []


# ---------------------------------------------------------------------------
# Domain input models
# ---------------------------------------------------------------------------


class TemperatureScenario(BaseModel):
    indoor_temp_c: float = Field(default=20.0)
    outdoor_temp_c: float = Field(default=-10.0)


class AirtightnessAssumption(BaseModel):
    ach_low: float = Field(gt=0)
    ach_base: float = Field(gt=0)
    ach_high: float = Field(gt=0)
    source: str


class EnvelopeAssemblyCandidate(BaseModel):
    name: str
    u_value_low: float = Field(gt=0)
    u_value_base: float = Field(gt=0)
    u_value_high: float = Field(gt=0)
    source: str
    confidence: float = Field(ge=0.0, le=1.0)


class HeatLossRequest(BaseModel):
    building_id: str
    building_type: BuildingType
    vision_result: VisionInput
    geometry_result: GeometryInput
    temperature_scenario: TemperatureScenario = Field(
        default_factory=TemperatureScenario
    )
    airtightness_override: AirtightnessAssumption | None = None
    user_notes: str | None = None


# ---------------------------------------------------------------------------
# Output models
# ---------------------------------------------------------------------------


class ComponentHeatLossRange(BaseModel):
    component: Literal["walls", "roof", "windows", "infiltration"]
    q_loss_w_low: float
    q_loss_w_base: float
    q_loss_w_high: float
    assumptions: list[str]


class SelectedEnvelopeModel(BaseModel):
    wall_assembly: EnvelopeAssemblyCandidate
    roof_assembly: EnvelopeAssemblyCandidate
    window_assembly: EnvelopeAssemblyCandidate
    airtightness: AirtightnessAssumption


class HeatLossSummary(BaseModel):
    delta_t_c: float
    transmission_loss_w_low: float
    transmission_loss_w_base: float
    transmission_loss_w_high: float
    infiltration_loss_w_low: float
    infiltration_loss_w_base: float
    infiltration_loss_w_high: float
    total_loss_w_low: float
    total_loss_w_base: float
    total_loss_w_high: float


class HeatLossResponse(BaseModel):
    building_id: str
    selected_model: SelectedEnvelopeModel
    component_losses: list[ComponentHeatLossRange]
    summary: HeatLossSummary
    warnings: list[str]
    disclaimers: list[str]
