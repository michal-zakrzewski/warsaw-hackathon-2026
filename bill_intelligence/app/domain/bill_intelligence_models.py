"""Pydantic v2 domain models for the bill-intelligence service."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class BillDocumentInput(BaseModel):
    document_id: str
    source_type: Literal["local_file", "gcs_uri", "base64"]
    file_path: str | None = None
    gcs_uri: str | None = None
    base64_content: str | None = None  # raw base64 string (no data:... prefix)
    mime_type: str
    file_name: str | None = None
    upload_timestamp: datetime | None = None


class BillEntity(BaseModel):
    type: str
    mention_text: str | None = None
    normalized_value: str | None = None
    confidence: float | None = None
    page_refs: list[int] = Field(default_factory=list)
    raw: dict = Field(default_factory=dict)


class BillExtractionResult(BaseModel):
    document_id: str
    processor_used: str
    processor_type: Literal["utility", "form", "custom", "unknown"]
    success: bool
    entities: list[BillEntity]
    text: str | None = None
    tables: list[dict] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    confidence: float
    raw_document: dict | None = None


class NormalizedBill(BaseModel):
    document_id: str
    provider_name: str | None = None
    account_number: str | None = None
    meter_number: str | None = None
    customer_name: str | None = None
    service_address: str | None = None
    billing_period_start: date | None = None
    billing_period_end: date | None = None
    billing_days: int | None = None
    currency: str | None = None
    total_amount: float | None = None
    previous_balance: float | None = None
    electricity_import_kwh: float | None = None
    electricity_export_kwh: float | None = None
    peak_kwh: float | None = None
    offpeak_kwh: float | None = None
    demand_kw: float | None = None
    energy_charge_amount: float | None = None
    delivery_charge_amount: float | None = None
    fixed_charge_amount: float | None = None
    taxes_amount: float | None = None
    import_rate_per_kwh: float | None = None
    export_credit_per_kwh: float | None = None
    document_confidence: float
    extraction_notes: list[str] = Field(default_factory=list)
    source_document_ids: list[str] = Field(default_factory=list)


class HistoricalBillPortfolio(BaseModel):
    bills: list[NormalizedBill]


class MonthlyConsumptionPoint(BaseModel):
    month: str  # "YYYY-MM"
    import_kwh: float | None = None
    export_kwh: float | None = None
    total_amount: float | None = None


class BillPortfolioSummary(BaseModel):
    document_count: int
    valid_bill_count: int
    coverage_start: date | None = None
    coverage_end: date | None = None
    covered_days: int
    annualized_import_kwh: float | None = None
    annualized_export_kwh: float | None = None
    annualized_bill_cost: float | None = None
    blended_import_rate_per_kwh: float | None = None
    blended_export_credit_per_kwh: float | None = None
    average_monthly_bill: float | None = None
    monthly_profile: list[MonthlyConsumptionPoint] = Field(default_factory=list)
    confidence: float
    warnings: list[str] = Field(default_factory=list)
    provenance: list[dict] = Field(default_factory=list)


class DerivedComparisonInputs(BaseModel):
    annual_electricity_kwh: float | None = None
    annual_bill_cost: float | None = None
    electricity_import_rate_per_kwh: float | None = None
    electricity_export_rate_per_kwh: float | None = None
    confidence: float
    warnings: list[str] = Field(default_factory=list)
    provenance: list[dict] = Field(default_factory=list)


class BillIntelligenceRequest(BaseModel):
    building_id: str
    country_code: str | None = None
    documents: list[BillDocumentInput]
    expected_document_type: Literal["electricity_bill", "mixed", "unknown"] = "electricity_bill"
    annualization_mode: Literal["strict", "normalize_to_365"] = "normalize_to_365"
    allow_fallback_processor: bool = True
    include_raw_document: bool = False


class BillIntelligenceResponse(BaseModel):
    building_id: str
    extractions: list[BillExtractionResult]
    normalized_bills: list[NormalizedBill]
    portfolio_summary: BillPortfolioSummary
    derived_inputs: DerivedComparisonInputs
