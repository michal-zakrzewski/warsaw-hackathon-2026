from __future__ import annotations

from fastapi import FastAPI

from app.api.heat_loss import router as heat_loss_router

app = FastAPI(
    title="Heat Loss Engine",
    description=(
        "Deterministic building heat-loss pre-estimator. "
        "Computes transmission and infiltration losses from vision features, "
        "geometry estimates, and a temperature scenario. "
        "All results are low / base / high ranges — not a certified energy audit."
    ),
    version="0.1.0",
)

app.include_router(heat_loss_router)
