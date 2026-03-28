from __future__ import annotations

from fastapi import APIRouter

from app.domain.heat_loss_models import HeatLossRequest, HeatLossResponse
from app.services.heat_loss_engine import calculate

router = APIRouter(prefix="/heat-loss", tags=["heat-loss"])


@router.post("/calculate", response_model=HeatLossResponse)
def calculate_heat_loss(request: HeatLossRequest) -> HeatLossResponse:
    """Estimate building heat loss from vision features, geometry, and temperature scenario.

    Returns low / base / high ranges for each heat-loss component.
    Inspect ``warnings`` for data-quality issues and ``disclaimers`` for
    limitations of the pre-estimate methodology.
    """
    return calculate(request)
