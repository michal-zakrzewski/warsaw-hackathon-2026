"""Maps vision-service output to envelope assembly candidates with U-value ranges."""

from __future__ import annotations

from app.config.envelope_defaults import (
    INSULATION_U_MULTIPLIER,
    ROOF_ASSEMBLY_BY_COVERING,
    WALL_ASSEMBLY_BY_FINISH_OVERRIDE,
    WALL_ASSEMBLY_BY_STRUCTURE,
    WINDOW_ASSEMBLY_BY_TYPE,
)
from app.domain.heat_loss_models import EnvelopeAssemblyCandidate


def map_wall_assembly(
    wall_finish: str,
    wall_structure: str,
    visible_insulation: str,
    vision_confidence: float,
) -> EnvelopeAssemblyCandidate:
    """Select wall assembly candidate and apply insulation-visibility correction.

    Priority order:
    1. Finish-based override (sandwich_panel, glass_curtain) — these imply a
       specific assembly regardless of structural guess.
    2. Structure-based lookup.
    3. Fallback to "unknown" if neither key is found.
    """
    if wall_finish in WALL_ASSEMBLY_BY_FINISH_OVERRIDE:
        base = WALL_ASSEMBLY_BY_FINISH_OVERRIDE[wall_finish]
        # Finish overrides already encode insulation; skip multiplier for sandwich_panel.
        # glass_curtain can still be adjusted (it may or may not have thermal break).
        multiplier = (
            INSULATION_U_MULTIPLIER.get(visible_insulation, (1.0, 1.0, 1.0))
            if wall_finish == "glass_curtain"
            else (1.0, 1.0, 1.0)
        )
    else:
        base = WALL_ASSEMBLY_BY_STRUCTURE.get(
            wall_structure, WALL_ASSEMBLY_BY_STRUCTURE["unknown"]
        )
        multiplier = INSULATION_U_MULTIPLIER.get(visible_insulation, (1.0, 1.0, 1.0))

    low_m, base_m, high_m = multiplier
    return EnvelopeAssemblyCandidate(
        name=base.name,
        u_value_low=round(base.u_value_low * low_m, 3),
        u_value_base=round(base.u_value_base * base_m, 3),
        u_value_high=round(base.u_value_high * high_m, 3),
        source=base.source,
        confidence=round(min(base.confidence * (0.5 + 0.5 * vision_confidence), 1.0), 3),
    )


def map_roof_assembly(
    roof_covering: str,
    visible_insulation: str,
    vision_confidence: float,
) -> EnvelopeAssemblyCandidate:
    """Select roof assembly candidate and apply insulation-visibility correction."""
    base = ROOF_ASSEMBLY_BY_COVERING.get(
        roof_covering, ROOF_ASSEMBLY_BY_COVERING["unknown"]
    )
    low_m, base_m, high_m = INSULATION_U_MULTIPLIER.get(
        visible_insulation, (1.0, 1.0, 1.0)
    )
    return EnvelopeAssemblyCandidate(
        name=base.name,
        u_value_low=round(base.u_value_low * low_m, 3),
        u_value_base=round(base.u_value_base * base_m, 3),
        u_value_high=round(base.u_value_high * high_m, 3),
        source=base.source,
        confidence=round(min(base.confidence * (0.5 + 0.5 * vision_confidence), 1.0), 3),
    )


def map_window_assembly(
    window_type: str,
    vision_confidence: float,
) -> EnvelopeAssemblyCandidate:
    """Select window assembly candidate.

    Insulation-visibility adjustment is NOT applied to windows — the visible
    insulation signs field from vision refers to wall/roof insulation, not
    to the window glazing specification.
    """
    base = WINDOW_ASSEMBLY_BY_TYPE.get(window_type, WINDOW_ASSEMBLY_BY_TYPE["unknown"])
    return EnvelopeAssemblyCandidate(
        name=base.name,
        u_value_low=base.u_value_low,
        u_value_base=base.u_value_base,
        u_value_high=base.u_value_high,
        source=base.source,
        confidence=round(min(base.confidence * (0.5 + 0.5 * vision_confidence), 1.0), 3),
    )
