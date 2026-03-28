from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.domain.vision_models import (
    ConditionFlags,
    ImageInput,
    ImageQualityFlags,
    PerImageVisionResult,
)


@runtime_checkable
class VisionModelClient(Protocol):
    """Contract for any vision model backend (Gemini, GPT-4V, stub, …).

    Implementors receive a single image and a pre-built prompt and must return
    a fully populated PerImageVisionResult.  The caller is responsible for
    prompt construction; the client is responsible only for transport and
    response parsing.
    """

    def analyze_image(self, image: ImageInput, prompt: str) -> PerImageVisionResult:
        ...


class FakeVisionModelClient:
    """Deterministic stub for unit and integration tests.

    Returns plausible but hardcoded values derived from the image's view_type
    so that aggregation logic can be exercised without a live model.
    """

    def analyze_image(self, image: ImageInput, prompt: str) -> PerImageVisionResult:
        roof_visible = image.view_type in ("roof_oblique", "rear")
        facade_visible = image.view_type in ("front", "side")

        return PerImageVisionResult(
            image_id=image.image_id,
            wall_finish_material="plaster",
            wall_structure_guess="brick",
            roof_covering_material="ceramic_tile" if roof_visible else "unknown",
            roof_type="gable" if roof_visible else "unknown",
            window_type_guess="double_glazed" if facade_visible else "unknown",
            visible_insulation_signs="uncertain",
            condition_flags=ConditionFlags(
                cracks_visible="no",
                moisture_stains_visible="no",
                facade_degradation_visible="no",
                roof_damage_visible="no",
                thermal_bridge_risk_visible="uncertain",
            ),
            image_quality_flags=ImageQualityFlags(
                blurry=False,
                low_light=False,
                occluded=False,
                roof_not_visible=not roof_visible,
                facade_not_visible=not facade_visible,
                insufficient_detail=False,
            ),
            confidence=0.75,
            evidence=_fake_evidence(image.view_type),
            missing_information=_fake_missing(image.view_type),
        )


def _fake_evidence(view_type: str) -> list[str]:
    items: list[str] = [
        "Exterior finish appears to be plaster based on surface texture",
        "Brick structural walls inferred from window reveal depth",
    ]
    if view_type in ("roof_oblique", "rear"):
        items += [
            "Ceramic tile roof covering clearly visible",
            "Gable roof form confirmed from this angle",
        ]
    if view_type in ("front", "side"):
        items.append("Double-glazed window profile visible on facade")
    return items


def _fake_missing(view_type: str) -> list[str]:
    missing: list[str] = []
    if view_type not in ("roof_oblique", "rear"):
        missing.append("Roof covering and form not visible from this angle")
    if view_type not in ("front", "side"):
        missing.append("Window type cannot be determined from this angle")
    return missing
