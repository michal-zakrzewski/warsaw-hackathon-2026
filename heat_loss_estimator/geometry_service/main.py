from __future__ import annotations

from fastapi import FastAPI

from app.api.geometry import router as geometry_router

app = FastAPI(
    title="Geometry Service",
    description=(
        "Estimates building envelope geometry (wall area, roof area, heated volume, …) "
        "from user-supplied dimensions and vision-service output. "
        "All estimates are deterministic and expressed as low/base/high ranges."
    ),
    version="0.1.0",
)

app.include_router(geometry_router)
