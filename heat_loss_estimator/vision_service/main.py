from __future__ import annotations

from fastapi import FastAPI

from app.api.vision import router as vision_router

app = FastAPI(
    title="Vision Service",
    description="Extracts observable building envelope features from photographs.",
    version="0.1.0",
)

app.include_router(vision_router)
