from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

# Load .env from repo root (one level up from this file)
load_dotenv(Path(__file__).parent.parent / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.bill_intelligence import router as bill_router

app = FastAPI(
    title="Bill Intelligence Service",
    description=(
        "Processes energy bills via Google Cloud Document AI. "
        "Extracts, normalizes, and aggregates billing history into "
        "annual_electricity_kwh, annual_bill_cost, and tariff rates "
        "for use in Solar / Storage / Retrofit comparison modules."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

app.include_router(bill_router)
