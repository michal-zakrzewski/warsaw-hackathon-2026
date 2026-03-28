from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.clients.vision_model_client import VisionModelClient
from app.dependencies import get_vision_client
from app.domain.vision_models import VisionRequest, VisionResponse
from app.services.vision_service import VisionService

router = APIRouter(prefix="/vision", tags=["vision"])

_ClientDep = Annotated[VisionModelClient, Depends(get_vision_client)]


@router.post("/analyze", response_model=VisionResponse)
def analyze_building(
    request: VisionRequest,
    client: _ClientDep,
) -> VisionResponse:
    """Analyse building images and return extracted visual features.

    Accepts a VisionRequest with one or more images plus optional building
    context.  Each image is assessed independently and results are then
    aggregated into a single AggregatedVisionResult.
    """
    return VisionService(client).analyze(request)
