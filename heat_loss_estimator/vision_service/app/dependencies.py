from __future__ import annotations

import os

from app.clients.vision_model_client import (
    FakeVisionModelClient,
    GeminiVisionModelClient,
    VisionModelClient,
)


def get_vision_client() -> VisionModelClient:
    """FastAPI dependency that supplies the active VisionModelClient.

    Returns GeminiVisionModelClient when GOOGLE_API_KEY or GEMINI_API_KEY is
    set in the environment; falls back to FakeVisionModelClient otherwise.
    """
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if api_key:
        return GeminiVisionModelClient(api_key=api_key)
    return FakeVisionModelClient()
