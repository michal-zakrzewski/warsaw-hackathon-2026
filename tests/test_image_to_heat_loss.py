"""Integration test: image → Gemini vision → heat loss estimate.

No text description needed — Gemini analyses the photo and fills in all
building feature parameters automatically.

Setup
-----
1. Save the test building photo to:
       tests/fixtures/building_test.jpg

2. Ensure GOOGLE_API_KEY (or GEMINI_API_KEY) is set in the environment
   or in green_agent/.env

Run
---
    uv run pytest tests/test_image_to_heat_loss.py -v -s
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
ROOT = Path(__file__).parent.parent

# Load heat_loss_tools directly — avoids triggering green_agent/__init__.py
# which pulls in google.adk (not needed here).
_spec = importlib.util.spec_from_file_location(
    "heat_loss_tools",
    ROOT / "green_agent" / "heat_loss_tools.py",
)
_heat_loss_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_heat_loss_mod)
estimate_heat_loss = _heat_loss_mod.estimate_heat_loss

# ---------------------------------------------------------------------------
# Load .env so the test finds the API key without manual export
# ---------------------------------------------------------------------------
_env_file = (ROOT / "green_agent" / ".env") if (ROOT / "green_agent" / ".env").exists() else (ROOT / ".env")
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FIXTURE_IMAGE = ROOT / "tests" / "fixtures" / "building_test.jpg"

_VISION_PROMPT = """\
You are a building envelope assessment assistant.
Analyse the building photograph and return ONLY a JSON object — no markdown, \
no explanation, no extra keys.

Required fields:
{
  "building_type": "<house|apartment_block|office|warehouse|industrial|unknown>",
  "wall_finish_material": "<plaster|brick_face|concrete|wood|siding|sandwich_panel|glass_curtain|metal_cladding|unknown>",
  "wall_structure_guess": "<brick|concrete|aac|timber_frame|steel_frame|mixed|unknown>",
  "roof_covering_material": "<metal_sheet|ceramic_tile|concrete_tile|bitumen_membrane|shingle|green_roof|unknown>",
  "roof_type": "<flat|gable|hip|shed|mansard|sawtooth|unknown>",
  "window_type_guess": "<single_glazed|double_glazed|triple_glazed|mixed|unknown>",
  "visible_insulation_signs": "<yes|no|uncertain>",
  "cracks_visible": "<yes|no|uncertain>",
  "facade_degradation_visible": "<yes|no|uncertain>",
  "thermal_bridge_risk_visible": "<yes|no|uncertain>",
  "confidence": <float 0.0–1.0>
}
"""

# ---------------------------------------------------------------------------
# Skip markers
# ---------------------------------------------------------------------------

_missing_image = not FIXTURE_IMAGE.exists()
_missing_key = not (os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _analyze_image(image_path: Path) -> dict:
    """Call Gemini with the image and return the parsed feature dict."""
    from google import genai
    from google.genai import types

    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    raw = image_path.read_bytes()
    image_part = types.Part.from_bytes(data=raw, mime_type="image/jpeg")

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[_VISION_PROMPT, image_part],
    )

    text = response.text.strip()
    # Strip markdown fences if Gemini wraps the JSON anyway
    m = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    if m:
        text = m.group(1)

    return json.loads(text)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.skipif(_missing_image, reason=f"Save the test photo to {FIXTURE_IMAGE}")
@pytest.mark.skipif(_missing_key, reason="Set GOOGLE_API_KEY in green_agent/.env")
def test_image_to_heat_loss():
    """Full pipeline: photo → Gemini vision features → heat loss estimate."""
    # ── Step 1: vision ──────────────────────────────────────────────────────
    vision = _analyze_image(FIXTURE_IMAGE)

    print("\n── Vision result ──────────────────────────────────────────────")
    print(json.dumps(vision, indent=2))

    # Sanity: Gemini must return at least the key fields
    required_keys = {
        "building_type", "wall_finish_material", "wall_structure_guess",
        "roof_covering_material", "roof_type", "window_type_guess",
        "visible_insulation_signs", "confidence",
    }
    missing = required_keys - vision.keys()
    assert not missing, f"Gemini response missing keys: {missing}"

    # ── Step 2: heat loss ───────────────────────────────────────────────────
    result = estimate_heat_loss(
        building_type=vision.get("building_type", "unknown"),
        wall_finish_material=vision.get("wall_finish_material", "unknown"),
        wall_structure_guess=vision.get("wall_structure_guess", "unknown"),
        roof_covering_material=vision.get("roof_covering_material", "unknown"),
        roof_type=vision.get("roof_type", "unknown"),
        window_type_guess=vision.get("window_type_guess", "unknown"),
        visible_insulation_signs=vision.get("visible_insulation_signs", "uncertain"),
        cracks_visible=vision.get("cracks_visible", "uncertain"),
        facade_degradation_visible=vision.get("facade_degradation_visible", "uncertain"),
        thermal_bridge_risk_visible=vision.get("thermal_bridge_risk_visible", "uncertain"),
        vision_confidence=float(vision.get("confidence", 0.5)),
        # No dimensions supplied — the engine uses building-type defaults
        footprint_area_m2=None,
        building_length_m=None,
        building_width_m=None,
        floors_count=None,
        floor_height_m=None,
        window_to_wall_ratio_hint=None,
        indoor_temp_c=20.0,
        outdoor_temp_c=-10.0,  # PL winter design temperature
    )

    print("\n── Heat loss result ───────────────────────────────────────────")
    print(json.dumps(result, indent=2))

    # ── Step 3: assertions ──────────────────────────────────────────────────
    summary = result["summary"]

    assert summary["total_w"]["base"] > 0, "Base heat loss must be positive"
    assert summary["total_kw"]["low"] <= summary["total_kw"]["base"] <= summary["total_kw"]["high"], \
        "Range must be ordered low ≤ base ≤ high"

    # Uninsulated brick building at ΔT=30°C → expect at least 1 kW base loss
    assert summary["total_kw"]["base"] >= 1.0, (
        f"Expected ≥1 kW for uninsulated brick building, "
        f"got {summary['total_kw']['base']:.2f} kW"
    )

    assert isinstance(result["warnings"], list)
    assert len(result["disclaimers"]) >= 1
