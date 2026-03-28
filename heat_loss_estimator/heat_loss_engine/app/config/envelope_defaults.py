"""Building physics constants and material lookup tables.

All U-values in W/(m²·K), ACH in h⁻¹.

Sources:
- EN ISO 6946:2017 (component thermal resistance)
- EN 12831-1:2017 (design heat load)
- Typical Central European building stock data (Polish NBI, TABULA project)
- ASHRAE Handbook of Fundamentals (infiltration)
"""

from __future__ import annotations

from app.domain.heat_loss_models import AirtightnessAssumption, EnvelopeAssemblyCandidate

# ---------------------------------------------------------------------------
# Physical constant
# ---------------------------------------------------------------------------

# Volumetric heat capacity of air used in infiltration formula:
# Q [W] = AIR_FACTOR * ACH [h⁻¹] * V [m³] * ΔT [K]
# Derivation: ρ_air * c_p / 3600 ≈ 1.20 kg/m³ * 1006 J/(kg·K) / 3600 s/h ≈ 0.335 → rounded to 0.33
AIR_HEAT_CAPACITY_FACTOR: float = 0.33

# ---------------------------------------------------------------------------
# Wall assemblies — primary key: wall_structure_guess
# U-value ranges reflect era/insulation uncertainty for each structural type.
# ---------------------------------------------------------------------------

WALL_ASSEMBLY_BY_STRUCTURE: dict[str, EnvelopeAssemblyCandidate] = {
    "brick": EnvelopeAssemblyCandidate(
        name="Brick masonry wall (solid or cavity, era unknown)",
        u_value_low=0.80,
        u_value_base=1.60,
        u_value_high=2.50,
        source="EN ISO 6946; TABULA PL — solid brick 1.6–2.5, cavity 0.8–1.3 W/m²K",
        confidence=0.65,
    ),
    "concrete": EnvelopeAssemblyCandidate(
        name="Concrete wall (cast-in-place or precast panel)",
        u_value_low=0.80,
        u_value_base=1.40,
        u_value_high=2.20,
        source="TABULA PL — large panel construction 1.0–2.2 W/m²K",
        confidence=0.65,
    ),
    "aac": EnvelopeAssemblyCandidate(
        name="Autoclaved aerated concrete (AAC) block wall",
        u_value_low=0.25,
        u_value_base=0.50,
        u_value_high=0.90,
        source="Manufacturer data + EN ISO 6946; AAC λ ≈ 0.09–0.16 W/mK",
        confidence=0.70,
    ),
    "timber_frame": EnvelopeAssemblyCandidate(
        name="Timber frame wall (insulation level unknown)",
        u_value_low=0.20,
        u_value_base=0.45,
        u_value_high=1.00,
        source="EN ISO 6946; range covers uninsulated (1.0) to well-insulated (0.2) frame",
        confidence=0.60,
    ),
    "steel_frame": EnvelopeAssemblyCandidate(
        name="Steel frame with envelope infill (type unknown)",
        u_value_low=0.40,
        u_value_base=1.00,
        u_value_high=2.50,
        source="Wide range: insulated steel sandwich to uninsulated corrugated sheet",
        confidence=0.50,
    ),
    "mixed": EnvelopeAssemblyCandidate(
        name="Mixed / composite wall construction",
        u_value_low=0.50,
        u_value_base=1.20,
        u_value_high=2.50,
        source="Blend of typical values; high uncertainty due to mixed materials",
        confidence=0.50,
    ),
    "unknown": EnvelopeAssemblyCandidate(
        name="Unknown wall construction",
        u_value_low=0.50,
        u_value_base=1.50,
        u_value_high=3.00,
        source="Default fallback — very wide range; all assembly types possible",
        confidence=0.35,
    ),
}

# Finish-material overrides (take precedence over structure-based lookup).
# Only applied when the finish itself implies a specific assembly type.
WALL_ASSEMBLY_BY_FINISH_OVERRIDE: dict[str, EnvelopeAssemblyCandidate] = {
    "sandwich_panel": EnvelopeAssemblyCandidate(
        name="Insulated sandwich panel (PIR/PUR core)",
        u_value_low=0.15,
        u_value_base=0.30,
        u_value_high=0.50,
        source="Manufacturer data — sandwich panels λ_core ≈ 0.022–0.025 W/mK",
        confidence=0.80,
    ),
    "glass_curtain": EnvelopeAssemblyCandidate(
        name="Glass curtain wall (frameless or framed)",
        u_value_low=1.00,
        u_value_base=2.00,
        u_value_high=3.50,
        source="EN ISO 10077; modern triple-unit 1.0, older single-unit 3.5 W/m²K",
        confidence=0.65,
    ),
}

# ---------------------------------------------------------------------------
# Roof assemblies — primary key: roof_covering_material
# ---------------------------------------------------------------------------

ROOF_ASSEMBLY_BY_COVERING: dict[str, EnvelopeAssemblyCandidate] = {
    "metal_sheet": EnvelopeAssemblyCandidate(
        name="Metal sheet roof (insulation level unknown)",
        u_value_low=0.30,
        u_value_base=1.20,
        u_value_high=3.50,
        source="Range: insulated industrial roof 0.3 to uninsulated corrugated iron 3.5 W/m²K",
        confidence=0.50,
    ),
    "ceramic_tile": EnvelopeAssemblyCandidate(
        name="Ceramic tiled pitched roof (insulated attic assumed)",
        u_value_low=0.15,
        u_value_base=0.45,
        u_value_high=1.00,
        source="EN ISO 6946; tile + rafter + insulation — insulation thickness unknown",
        confidence=0.65,
    ),
    "concrete_tile": EnvelopeAssemblyCandidate(
        name="Concrete tiled pitched roof (insulated attic assumed)",
        u_value_low=0.15,
        u_value_base=0.45,
        u_value_high=1.00,
        source="EN ISO 6946; similar to ceramic tile assembly",
        confidence=0.65,
    ),
    "bitumen_membrane": EnvelopeAssemblyCandidate(
        name="Flat roof with bitumen membrane (inverted or warm deck)",
        u_value_low=0.15,
        u_value_base=0.50,
        u_value_high=1.20,
        source="EN ISO 6946; depends on insulation board thickness below membrane",
        confidence=0.65,
    ),
    "shingle": EnvelopeAssemblyCandidate(
        name="Shingle roof (insulated attic assumed)",
        u_value_low=0.20,
        u_value_base=0.55,
        u_value_high=1.20,
        source="EN ISO 6946; similar to ceramic tile; shingle common in timber-frame buildings",
        confidence=0.65,
    ),
    "green_roof": EnvelopeAssemblyCandidate(
        name="Green / sedum roof (typically well-insulated substrate)",
        u_value_low=0.10,
        u_value_base=0.20,
        u_value_high=0.40,
        source="Green roofs typically require ≥100 mm insulation by regulation; low U expected",
        confidence=0.70,
    ),
    "unknown": EnvelopeAssemblyCandidate(
        name="Unknown roof assembly",
        u_value_low=0.20,
        u_value_base=0.80,
        u_value_high=2.50,
        source="Default fallback — very wide range",
        confidence=0.35,
    ),
}

# ---------------------------------------------------------------------------
# Window assemblies — primary key: window_type_guess
# U-values represent the whole-window value (frame + glazing) per EN ISO 10077
# ---------------------------------------------------------------------------

WINDOW_ASSEMBLY_BY_TYPE: dict[str, EnvelopeAssemblyCandidate] = {
    "single_glazed": EnvelopeAssemblyCandidate(
        name="Single glazed window (clear glass, metal or wood frame)",
        u_value_low=4.00,
        u_value_base=5.00,
        u_value_high=6.00,
        source="EN ISO 10077; single 4 mm clear glass U_g ≈ 5.8 W/m²K, frame effect",
        confidence=0.80,
    ),
    "double_glazed": EnvelopeAssemblyCandidate(
        name="Double glazed window (air or argon fill, Low-E possible)",
        u_value_low=1.00,
        u_value_base=2.00,
        u_value_high=3.00,
        source="EN ISO 10077; old air-filled 2.8–3.0, modern Low-E argon 1.0–1.4 W/m²K",
        confidence=0.70,
    ),
    "triple_glazed": EnvelopeAssemblyCandidate(
        name="Triple glazed window (argon/krypton, Low-E coatings)",
        u_value_low=0.50,
        u_value_base=0.80,
        u_value_high=1.20,
        source="EN ISO 10077; triple Low-E argon 0.5–1.0, high-end krypton 0.5 W/m²K",
        confidence=0.75,
    ),
    "mixed": EnvelopeAssemblyCandidate(
        name="Mixed glazing (combination of single and double glazed)",
        u_value_low=1.50,
        u_value_base=3.00,
        u_value_high=5.00,
        source="Weighted blend of single and double glazed defaults",
        confidence=0.55,
    ),
    "unknown": EnvelopeAssemblyCandidate(
        name="Unknown window type",
        u_value_low=1.00,
        u_value_base=3.00,
        u_value_high=6.00,
        source="Default fallback — spans single to triple glazed range",
        confidence=0.30,
    ),
}

# ---------------------------------------------------------------------------
# Airtightness (ACH) defaults — primary key: building_type
# ACH = air changes per hour at natural pressure differential (not blower door)
# ---------------------------------------------------------------------------

ACH_BY_BUILDING_TYPE: dict[str, AirtightnessAssumption] = {
    "house": AirtightnessAssumption(
        ach_low=0.30,
        ach_base=0.70,
        ach_high=1.50,
        source="Typical detached house; ASHRAE 62.2 + TABULA PL stock data",
    ),
    "apartment_block": AirtightnessAssumption(
        ach_low=0.20,
        ach_base=0.50,
        ach_high=1.00,
        source="Apartment block — shared envelope reduces exposed area per unit",
    ),
    "office": AirtightnessAssumption(
        ach_low=0.30,
        ach_base=0.60,
        ach_high=1.20,
        source="Office building — mechanical ventilation often present; natural infiltration only",
    ),
    "warehouse": AirtightnessAssumption(
        ach_low=0.50,
        ach_base=1.00,
        ach_high=2.50,
        source="Warehouse — large doors, loading bays; high infiltration expected",
    ),
    "industrial": AirtightnessAssumption(
        ach_low=0.50,
        ach_base=1.20,
        ach_high=3.00,
        source="Industrial — process openings, high infiltration; very wide range",
    ),
    "unknown": AirtightnessAssumption(
        ach_low=0.30,
        ach_base=0.80,
        ach_high=2.00,
        source="Unknown building type — wide default range",
    ),
}

# ---------------------------------------------------------------------------
# Insulation visibility adjustments — multipliers on (u_low, u_base, u_high)
# Applied to walls and roof assemblies only (not windows).
# ---------------------------------------------------------------------------

# "yes"  = visible external insulation (e.g. EWI system, visible insulation boards)
# "no"   = no external insulation signs visible (internal insulation still possible)
# "uncertain" = no adjustment
INSULATION_U_MULTIPLIER: dict[str, tuple[float, float, float]] = {
    "yes": (0.90, 0.60, 0.70),
    "no": (1.00, 1.10, 1.30),
    "uncertain": (1.00, 1.00, 1.00),
}

# ---------------------------------------------------------------------------
# Standard disclaimers (always attached to every response)
# ---------------------------------------------------------------------------

DISCLAIMERS: list[str] = [
    "This is a pre-estimate only and does not constitute a certified energy audit.",
    "Results are based on visual assessment and heuristic defaults; they do not replace"
    " detailed on-site inspection or in-situ measurements.",
    "Standard photographs cannot reliably reveal hidden insulation, thermal bridges,"
    " or airtightness defects.",
    "For a reliable energy performance assessment, thermographic surveys,"
    " blower-door testing, and material specification data are recommended.",
]
