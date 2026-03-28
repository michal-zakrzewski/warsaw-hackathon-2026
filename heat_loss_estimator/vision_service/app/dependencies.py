from __future__ import annotations

from app.clients.vision_model_client import FakeVisionModelClient, VisionModelClient


def get_vision_client() -> VisionModelClient:
    """FastAPI dependency that supplies the active VisionModelClient.

    Replace the returned instance with a real Gemini (or other) client once
    the vision connector is implemented.
    """
    return FakeVisionModelClient()
