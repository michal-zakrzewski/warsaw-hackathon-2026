from __future__ import annotations

from app.domain.vision_models import ImageInput, VisionRequest

_RESPONSE_SCHEMA = """\
{
  "image_id": "<string — must match the provided image_id>",
  "wall_finish_material": "<one of: plaster | brick_face | concrete | wood | siding | sandwich_panel | glass_curtain | metal_cladding | unknown>",
  "wall_structure_guess": "<one of: brick | concrete | aac | timber_frame | steel_frame | mixed | unknown>",
  "roof_covering_material": "<one of: metal_sheet | ceramic_tile | concrete_tile | bitumen_membrane | shingle | green_roof | unknown>",
  "roof_type": "<one of: flat | gable | hip | shed | mansard | sawtooth | unknown>",
  "window_type_guess": "<one of: single_glazed | double_glazed | triple_glazed | mixed | unknown>",
  "visible_insulation_signs": "<one of: yes | no | uncertain>",
  "condition_flags": {
    "cracks_visible": "<one of: yes | no | uncertain>",
    "moisture_stains_visible": "<one of: yes | no | uncertain>",
    "facade_degradation_visible": "<one of: yes | no | uncertain>",
    "roof_damage_visible": "<one of: yes | no | uncertain>",
    "thermal_bridge_risk_visible": "<one of: yes | no | uncertain>"
  },
  "image_quality_flags": {
    "blurry": <true | false>,
    "low_light": <true | false>,
    "occluded": <true | false>,
    "roof_not_visible": <true | false>,
    "facade_not_visible": <true | false>,
    "insufficient_detail": <true | false>
  },
  "confidence": <float 0.0–1.0>,
  "evidence": ["<specific visual observation>", "…"],
  "missing_information": ["<feature that cannot be determined from this image>", "…"]
}\
"""

_RULES = """\
1. Report ONLY what is directly observable in the image. Do not infer beyond what you can see.
2. Use "unknown" for any enum field where the feature is not visible or indeterminate.
3. Use "uncertain" for ternary fields when evidence is ambiguous.
4. Set confidence to reflect your overall certainty (0 = pure guess, 1 = unambiguous observation).
5. Populate "evidence" with precise visual cues that support each classification.
6. Populate "missing_information" with features you cannot assess from this image.
7. Set quality flags accurately — they are used downstream to decide whether more images are needed.
8. Do NOT infer materials from building type or location stereotypes alone.\
"""


def build_vision_prompt(image: ImageInput, request: VisionRequest) -> str:
    """Build a structured prompt instructing the vision model to assess a single building image.

    The prompt embeds image metadata and building context, enforces the
    observed-vs-inferred discipline, and specifies the exact JSON schema the
    model must return.
    """
    context_lines: list[str] = [
        f"Building type hint : {request.building_type_hint}",
    ]
    if request.country_code:
        context_lines.append(f"Country code        : {request.country_code}")
    if request.user_notes:
        context_lines.append(f"User notes          : {request.user_notes}")
    if image.notes:
        context_lines.append(f"Image notes         : {image.notes}")

    context_block = "\n".join(context_lines)

    return (
        "You are a building envelope assessment assistant.\n"
        "Your task is to analyse a single building photograph and extract "
        "observable physical features relevant to thermal performance.\n\n"
        "IMAGE METADATA\n"
        "--------------\n"
        f"Image ID  : {image.image_id}\n"
        f"View type : {image.view_type}\n"
        f"{context_block}\n\n"
        "RULES\n"
        "-----\n"
        f"{_RULES}\n\n"
        "REQUIRED RESPONSE FORMAT\n"
        "------------------------\n"
        "Return ONLY a single JSON object matching the schema below. "
        "No explanation, no markdown fences.\n\n"
        f"{_RESPONSE_SCHEMA}\n"
    )
