"""Deterministic orchestrator: extract → normalize → aggregate → derive."""

from __future__ import annotations

from app.clients.documentai_client import DocumentAIClientProtocol
from app.domain.bill_intelligence_models import (
    BillDocumentInput,
    BillExtractionResult,
    BillIntelligenceRequest,
    BillIntelligenceResponse,
    NormalizedBill,
)
from app.services.bill_history_aggregator import aggregate_bill_history
from app.services.bill_normalizer import normalize_bill
from app.services.derive_comparison_inputs import derive_comparison_inputs


class BillIntelligenceAgent:
    """Runs the four-step bill intelligence pipeline deterministically.

    Step 1 — extract_bill_document : Document AI → BillExtractionResult
    Step 2 — normalize_bill        : entities → NormalizedBill
    Step 3 — aggregate_bill_history: list[NormalizedBill] → BillPortfolioSummary
    Step 4 — derive_comparison_inputs: summary → DerivedComparisonInputs
    """

    def __init__(self, client: DocumentAIClientProtocol) -> None:
        self._client = client

    def run(self, request: BillIntelligenceRequest) -> BillIntelligenceResponse:
        extractions   = self._step_extract(request)
        normalized    = self._step_normalize(extractions)
        summary       = aggregate_bill_history(normalized, request.annualization_mode)
        derived       = derive_comparison_inputs(summary)

        return BillIntelligenceResponse(
            building_id=request.building_id,
            extractions=extractions,
            normalized_bills=normalized,
            portfolio_summary=summary,
            derived_inputs=derived,
        )

    # ------------------------------------------------------------------
    # Steps
    # ------------------------------------------------------------------

    def _step_extract(
        self, request: BillIntelligenceRequest
    ) -> list[BillExtractionResult]:
        results: list[BillExtractionResult] = []
        for doc in request.documents:
            result = self._extract_bill_document(
                doc,
                allow_fallback=request.allow_fallback_processor,
                include_raw=request.include_raw_document,
            )
            results.append(result)
        return results

    def _step_normalize(
        self, extractions: list[BillExtractionResult]
    ) -> list[NormalizedBill]:
        normalized: list[NormalizedBill] = []
        for extraction in extractions:
            if extraction.success:
                normalized.append(normalize_bill(extraction))
        return normalized

    def extract_bill_document(
        self,
        document: BillDocumentInput,
        allow_fallback: bool = True,
        include_raw: bool = False,
    ) -> BillExtractionResult:
        """Public single-document extraction entry point."""
        return self._extract_bill_document(document, allow_fallback, include_raw)

    def _extract_bill_document(
        self,
        document: BillDocumentInput,
        allow_fallback: bool,
        include_raw: bool,
    ) -> BillExtractionResult:
        if allow_fallback:
            return self._client.process_document_with_fallback(document, include_raw)
        return self._client.process_document(document, include_raw)
