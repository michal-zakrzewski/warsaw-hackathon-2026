"""Maps building condition and type to an airtightness (ACH) assumption."""

from __future__ import annotations

from app.config.envelope_defaults import ACH_BY_BUILDING_TYPE
from app.domain.heat_loss_models import AirtightnessAssumption, ConditionFlagsInput


def map_airtightness(
    building_type: str,
    visible_insulation: str,
    condition_flags: ConditionFlagsInput,
    override: AirtightnessAssumption | None,
) -> AirtightnessAssumption:
    """Return the effective AirtightnessAssumption for a building.

    If the caller provides an override, it is returned unchanged.
    Otherwise, the building-type default is adjusted based on visible
    condition indicators from the vision result.
    """
    if override is not None:
        return override

    base = ACH_BY_BUILDING_TYPE.get(building_type, ACH_BY_BUILDING_TYPE["unknown"])

    low_m = 1.0
    base_m = 1.0
    high_m = 1.0
    notes: list[str] = [f"Building type '{building_type}' default ACH range"]

    if condition_flags.cracks_visible == "yes":
        base_m *= 1.40
        high_m *= 1.60
        notes.append("Cracks visible → elevated air leakage assumed")
    elif condition_flags.cracks_visible == "uncertain":
        high_m *= 1.20

    if condition_flags.facade_degradation_visible == "yes":
        base_m *= 1.25
        high_m *= 1.35
        notes.append("Facade degradation visible → elevated infiltration")

    if visible_insulation == "yes":
        low_m *= 0.75
        base_m *= 0.75
        notes.append("Insulation signs visible → better-sealed envelope assumed")
    elif visible_insulation == "no":
        base_m *= 1.10
        high_m *= 1.20

    return AirtightnessAssumption(
        ach_low=round(base.ach_low * low_m, 3),
        ach_base=round(base.ach_base * base_m, 3),
        ach_high=round(base.ach_high * high_m, 3),
        source="; ".join(notes),
    )
