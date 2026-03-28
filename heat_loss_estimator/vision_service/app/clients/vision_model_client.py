from __future__ import annotations

import json
import re
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


class GeminiVisionModelClient:
    """Real Gemini vision backend using google-genai SDK.

    Loads the image from URL or local file, sends it with the pre-built prompt,
    and parses the JSON response into a PerImageVisionResult.
    """

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash") -> None:
        self._api_key = api_key
        self._model_name = model

    def analyze_image(self, image: ImageInput, prompt: str) -> PerImageVisionResult:
        from google import genai  # type: ignore[import]
        from google.genai import types  # type: ignore[import]

        client = genai.Client(api_key=self._api_key)

        if image.source_type == "url" and image.image_url:
            import urllib.request

            with urllib.request.urlopen(image.image_url) as resp:
                raw = resp.read()
            mime = image.mime_type or "image/jpeg"
        elif image.source_type == "upload" and image.storage_path:
            with open(image.storage_path, "rb") as f:
                raw = f.read()
            mime = image.mime_type or "image/jpeg"
        else:
            return _unknown_result(image.image_id)

        image_part = types.Part.from_bytes(data=raw, mime_type=mime)
        response = client.models.generate_content(
            model=self._model_name,
            contents=[prompt, image_part],
        )
        return _parse_gemini_response(image.image_id, response.text)


def _parse_gemini_response(image_id: str, text: str) -> PerImageVisionResult:
    """Parse raw Gemini text into PerImageVisionResult, with fallback for bad JSON."""
    # Strip markdown fences if present
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    if match:
        text = match.group(1)

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Return a low-confidence unknown result rather than crashing
        return _unknown_result(image_id)

    try:
        return PerImageVisionResult(
            image_id=image_id,
            wall_finish_material=data.get("wall_finish_material", "unknown"),
            wall_structure_guess=data.get("wall_structure_guess", "unknown"),
            roof_covering_material=data.get("roof_covering_material", "unknown"),
            roof_type=data.get("roof_type", "unknown"),
            window_type_guess=data.get("window_type_guess", "unknown"),
            visible_insulation_signs=data.get("visible_insulation_signs", "uncertain"),
            condition_flags=ConditionFlags(
                cracks_visible=data.get("condition_flags", {}).get("cracks_visible", "uncertain"),
                moisture_stains_visible=data.get("condition_flags", {}).get("moisture_stains_visible", "uncertain"),
                facade_degradation_visible=data.get("condition_flags", {}).get("facade_degradation_visible", "uncertain"),
                roof_damage_visible=data.get("condition_flags", {}).get("roof_damage_visible", "uncertain"),
                thermal_bridge_risk_visible=data.get("condition_flags", {}).get("thermal_bridge_risk_visible", "uncertain"),
            ),
            image_quality_flags=ImageQualityFlags(
                blurry=data.get("image_quality_flags", {}).get("blurry", False),
                low_light=data.get("image_quality_flags", {}).get("low_light", False),
                occluded=data.get("image_quality_flags", {}).get("occluded", False),
                roof_not_visible=data.get("image_quality_flags", {}).get("roof_not_visible", False),
                facade_not_visible=data.get("image_quality_flags", {}).get("facade_not_visible", False),
                insufficient_detail=data.get("image_quality_flags", {}).get("insufficient_detail", False),
            ),
            confidence=float(data.get("confidence", 0.5)),
            evidence=data.get("evidence", []),
            missing_information=data.get("missing_information", []),
        )
    except Exception:
        return _unknown_result(image_id)


def _unknown_result(image_id: str) -> PerImageVisionResult:
    return PerImageVisionResult(
        image_id=image_id,
        wall_finish_material="unknown",
        wall_structure_guess="unknown",
        roof_covering_material="unknown",
        roof_type="unknown",
        window_type_guess="unknown",
        visible_insulation_signs="uncertain",
        condition_flags=ConditionFlags(
            cracks_visible="uncertain",
            moisture_stains_visible="uncertain",
            facade_degradation_visible="uncertain",
            roof_damage_visible="uncertain",
            thermal_bridge_risk_visible="uncertain",
        ),
        image_quality_flags=ImageQualityFlags(
            blurry=False, low_light=False, occluded=False,
            roof_not_visible=True, facade_not_visible=True, insufficient_detail=True,
        ),
        confidence=0.1,
        evidence=[],
        missing_information=["Model response could not be parsed"],
    )
