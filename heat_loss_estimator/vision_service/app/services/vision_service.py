from __future__ import annotations

from app.clients.vision_model_client import VisionModelClient
from app.domain.vision_models import VisionRequest, VisionResponse
from app.prompts.vision_prompt_builder import build_vision_prompt
from app.services.vision_aggregator import aggregate_results


class VisionService:
    """Orchestrates per-image analysis and result aggregation for a building."""

    def __init__(self, client: VisionModelClient) -> None:
        self._client = client

    def analyze(self, request: VisionRequest) -> VisionResponse:
        per_image_results = [
            self._client.analyze_image(
                image,
                build_vision_prompt(image, request),
            )
            for image in request.images
        ]

        aggregated = aggregate_results(per_image_results, request.images)

        return VisionResponse(
            building_id=request.building_id,
            per_image_results=per_image_results,
            aggregated=aggregated,
        )
