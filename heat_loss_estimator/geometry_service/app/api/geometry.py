from __future__ import annotations

from fastapi import APIRouter

from app.domain.geometry_models import GeometryRequest, GeometryResponse
from app.services.geometry_service import estimate_geometry

router = APIRouter(prefix="/geometry", tags=["geometry"])


@router.post("/estimate", response_model=GeometryResponse)
def estimate_building_geometry(request: GeometryRequest) -> GeometryResponse:
    """Estimate building envelope geometry from user-supplied dimensions and vision output.

    All results are expressed as low / base / high ranges.  The wider the
    range, the less data was available.  Inspect the ``warnings`` and
    ``assumptions`` fields to understand what was inferred vs. measured.
    """
    return estimate_geometry(request)
