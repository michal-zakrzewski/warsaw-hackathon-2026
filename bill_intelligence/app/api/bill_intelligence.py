"""FastAPI router for the bill intelligence endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.clients.documentai_client import DocumentAIClientProtocol
from app.domain.bill_intelligence_models import BillIntelligenceRequest, BillIntelligenceResponse
from app.services.bill_intelligence_agent import BillIntelligenceAgent


router = APIRouter(prefix="/bill-intelligence", tags=["bill-intelligence"])


def _get_client() -> DocumentAIClientProtocol:
    """FastAPI dependency: returns the configured Document AI client."""
    from app.clients.documentai_client import FakeDocumentAIClient, GoogleDocumentAIClient
    from app.config.settings import get_settings

    settings = get_settings()

    if settings.use_fake_documentai:
        return FakeDocumentAIClient()

    missing = settings.validate_for_real_client()
    if missing:
        raise RuntimeError(
            f"Cannot initialize GoogleDocumentAIClient — missing env vars: {missing}. "
            "Set USE_FAKE_DOCUMENTAI=true to use the stub."
        )

    return GoogleDocumentAIClient(
        project_id=settings.google_cloud_project,
        location=settings.documentai_location,
        primary_processor_id=settings.documentai_primary_processor_id,
        primary_processor_type=settings.documentai_primary_processor_type,
        fallback_processor_id=settings.documentai_fallback_processor_id,
    )


@router.post("/process", response_model=BillIntelligenceResponse)
def process_bills(
    request: BillIntelligenceRequest,
    client: DocumentAIClientProtocol = Depends(_get_client),
) -> BillIntelligenceResponse:
    """Process one or more energy bill documents and return normalized intelligence.

    The pipeline runs deterministically:
    1. Extract entities via Document AI (utility parser, with optional form-parser fallback)
    2. Normalize entities to structured NormalizedBill objects
    3. Aggregate the bill history into portfolio-level statistics
    4. Derive the comparison inputs needed by Solar / Retrofit modules
    """
    agent = BillIntelligenceAgent(client)
    return agent.run(request)
