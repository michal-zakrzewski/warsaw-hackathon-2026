"""Document AI client — Protocol + Google Cloud implementation + Fake stub."""

from __future__ import annotations

import base64
import uuid
from typing import Protocol, runtime_checkable

from app.domain.bill_intelligence_models import BillDocumentInput, BillExtractionResult


@runtime_checkable
class DocumentAIClientProtocol(Protocol):
    """Contract for any Document AI backend."""

    def process_document(
        self,
        document: BillDocumentInput,
        include_raw: bool = False,
    ) -> BillExtractionResult:
        ...

    def process_document_with_fallback(
        self,
        document: BillDocumentInput,
        include_raw: bool = False,
    ) -> BillExtractionResult:
        ...


class GoogleDocumentAIClient:
    """Real Google Cloud Document AI client.

    Uses Application Default Credentials / service account configured in the
    environment.  Does NOT create processors at runtime — processor IDs are
    supplied via configuration.

    Supports both Form Parser and Utility Document Parser as the primary
    processor, with an optional fallback to a second processor.
    """

    def __init__(
        self,
        project_id: str,
        location: str,
        primary_processor_id: str,
        primary_processor_type: str = "form",
        fallback_processor_id: str | None = None,
    ) -> None:
        from google.api_core.client_options import ClientOptions  # type: ignore[import]
        from google.cloud import documentai  # type: ignore[import]

        self._project_id = project_id
        self._location = location
        self._primary_processor_id = primary_processor_id
        self._primary_processor_type = primary_processor_type
        self._fallback_processor_id = fallback_processor_id

        opts = ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")
        self._client = documentai.DocumentProcessorServiceClient(client_options=opts)

    def _processor_name(self, processor_id: str) -> str:
        return self._client.processor_path(
            self._project_id, self._location, processor_id
        )

    def process_document(
        self,
        document: BillDocumentInput,
        include_raw: bool = False,
    ) -> BillExtractionResult:
        return self._process(
            document,
            self._primary_processor_id,
            self._primary_processor_type,
            include_raw,
        )

    def process_document_with_fallback(
        self,
        document: BillDocumentInput,
        include_raw: bool = False,
    ) -> BillExtractionResult:
        result = self.process_document(document, include_raw)

        needs_fallback = (
            not result.success
            or result.confidence < 0.4
            or not result.entities
        )

        if needs_fallback and self._fallback_processor_id:
            fallback_type = (
                "utility" if self._primary_processor_type == "form" else "form"
            )
            fallback = self._process(
                document,
                self._fallback_processor_id,
                fallback_type,
                include_raw,
            )
            if fallback.success and fallback.confidence >= result.confidence:
                fallback.warnings.insert(
                    0,
                    f"Primary processor confidence {result.confidence:.2f} below threshold "
                    "— fell back to secondary processor",
                )
                return fallback

        return result

    def _process(
        self,
        document: BillDocumentInput,
        processor_id: str,
        processor_type: str,
        include_raw: bool,
    ) -> BillExtractionResult:
        from google.cloud import documentai  # type: ignore[import]

        from app.services.documentai_response_mapper import map_document_ai_response

        try:
            name = self._processor_name(processor_id)
            raw_document, gcs_document = self._build_document_source(document)

            if gcs_document:
                request = documentai.ProcessRequest(
                    name=name, gcs_document=gcs_document
                )
            else:
                request = documentai.ProcessRequest(
                    name=name, raw_document=raw_document
                )

            result = self._client.process_document(request=request)
            return map_document_ai_response(
                doc_result=result.document,
                document_id=document.document_id,
                processor_id=processor_id,
                processor_type=processor_type,  # type: ignore[arg-type]
                include_raw=include_raw,
            )
        except Exception as exc:
            return BillExtractionResult(
                document_id=document.document_id,
                processor_used=processor_id,
                processor_type="unknown",  # type: ignore[arg-type]
                success=False,
                entities=[],
                confidence=0.0,
                warnings=[f"Document AI call failed: {exc}"],
            )

    def _build_document_source(self, document: BillDocumentInput):
        from google.cloud import documentai  # type: ignore[import]

        if document.source_type == "local_file":
            raise ValueError(
                "local_file source type is disabled for security — use base64 instead"
            )

        if document.source_type == "gcs_uri" and document.gcs_uri:
            return None, documentai.GcsDocument(
                gcs_uri=document.gcs_uri, mime_type=document.mime_type
            )

        if document.source_type == "base64" and document.base64_content:
            content = base64.b64decode(document.base64_content)
        else:
            raise ValueError(
                f"Cannot resolve document source for document_id={document.document_id}"
            )

        return (
            documentai.RawDocument(content=content, mime_type=document.mime_type),
            None,
        )


class FakeDocumentAIClient:
    """Deterministic stub returning pre-baked entity sets.

    Cycles through a 3-month sequence so tests can build realistic portfolios
    without real Document AI credentials.
    """

    _MONTHS = [
        ("2024-01-01", "2024-01-31", 31, 312.5, 87.40, 245.00, 43.75, 24.50),
        ("2024-02-01", "2024-02-29", 29, 289.0, 80.92, 226.80, 40.46, 22.66),
        ("2024-03-01", "2024-03-31", 31, 275.3, 77.08, 215.50, 38.54, 21.64),
        ("2024-04-01", "2024-04-30", 30, 241.0, 67.48, 188.50, 33.74, 18.96),
        ("2024-05-01", "2024-05-31", 31, 198.5, 55.58, 155.30, 27.79, 15.58),
        ("2024-06-01", "2024-06-30", 30, 185.0, 51.80, 144.70, 25.90, 14.52),
        ("2024-07-01", "2024-07-31", 31, 192.0, 53.76, 150.20, 26.88, 15.08),
        ("2024-08-01", "2024-08-31", 31, 201.5, 56.42, 157.60, 28.21, 15.82),
        ("2024-09-01", "2024-09-30", 30, 220.0, 61.60, 172.20, 30.80, 17.28),
        ("2024-10-01", "2024-10-31", 31, 268.5, 75.18, 210.10, 37.59, 21.10),
        ("2024-11-01", "2024-11-30", 30, 305.0, 85.40, 238.70, 42.70, 23.96),
        ("2024-12-01", "2024-12-31", 31, 340.0, 95.20, 266.00, 47.60, 26.72),
    ]

    def __init__(self) -> None:
        self._call_count = 0

    def _month_row(self, idx: int) -> tuple:
        return self._MONTHS[idx % len(self._MONTHS)]

    def process_document(
        self,
        document: BillDocumentInput,
        include_raw: bool = False,
    ) -> BillExtractionResult:
        row = self._month_row(self._call_count)
        self._call_count += 1
        return self._make_result(document.document_id, row, "utility-fake-001", "utility")

    def process_document_with_fallback(
        self,
        document: BillDocumentInput,
        include_raw: bool = False,
    ) -> BillExtractionResult:
        return self.process_document(document, include_raw)

    def _make_result(
        self,
        document_id: str,
        row: tuple,
        processor_id: str,
        processor_type: str,
    ) -> BillExtractionResult:
        from app.domain.bill_intelligence_models import BillEntity

        (
            period_start, period_end, days,
            kwh, total_amount, energy_charge, fixed_charge, vat,
        ) = row

        entities = [
            BillEntity(type="supplier_name", mention_text="EnergiaPL S.A.", normalized_value="EnergiaPL S.A.", confidence=0.99),
            BillEntity(type="account_number", mention_text="ACC-20240001", normalized_value="ACC-20240001", confidence=0.99),
            BillEntity(type="customer_name", mention_text="Jan Kowalski", normalized_value="Jan Kowalski", confidence=0.97),
            BillEntity(type="service_address", mention_text="ul. Słoneczna 12, 00-001 Warszawa", normalized_value="ul. Słoneczna 12, 00-001 Warszawa", confidence=0.95),
            BillEntity(type="service_period_start", mention_text=period_start, normalized_value=period_start, confidence=0.98),
            BillEntity(type="service_period_end", mention_text=period_end, normalized_value=period_end, confidence=0.98),
            BillEntity(type="electricity_usage", mention_text=f"{kwh} kWh", normalized_value=str(kwh), confidence=0.96),
            BillEntity(type="total_amount", mention_text=f"{total_amount} PLN", normalized_value=str(total_amount), confidence=0.97),
            BillEntity(type="electricity_amount", mention_text=f"{energy_charge} PLN", normalized_value=str(energy_charge), confidence=0.94),
            BillEntity(type="fixed_charge", mention_text=f"{fixed_charge} PLN", normalized_value=str(fixed_charge), confidence=0.93),
            BillEntity(type="vat_amount", mention_text=f"{vat} PLN", normalized_value=str(vat), confidence=0.93),
            BillEntity(type="currency", mention_text="PLN", normalized_value="PLN", confidence=0.99),
        ]

        return BillExtractionResult(
            document_id=document_id,
            processor_used=processor_id,
            processor_type=processor_type,  # type: ignore[arg-type]
            success=True,
            entities=entities,
            text=f"Bill for period {period_start} to {period_end}. Usage: {kwh} kWh. Total: {total_amount} PLN.",
            confidence=0.95,
        )
