from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date

import pytest

from app.domain.bill_intelligence_models import BillEntity, BillExtractionResult
from app.services.bill_normalizer import normalize_bill


def _make_extraction(entities: list[BillEntity], document_id: str = "doc-001") -> BillExtractionResult:
    return BillExtractionResult(
        document_id=document_id,
        processor_used="utility-fake",
        processor_type="utility",
        success=True,
        entities=entities,
        confidence=0.92,
    )


def _entity(type_: str, normalized: str, confidence: float = 0.95) -> BillEntity:
    return BillEntity(type=type_, mention_text=normalized, normalized_value=normalized, confidence=confidence)


class TestDateParsing:
    def test_iso_date_parsed(self):
        extraction = _make_extraction([
            _entity("service_period_start", "2024-01-01"),
            _entity("service_period_end", "2024-01-31"),
        ])
        bill = normalize_bill(extraction)
        assert bill.billing_period_start == date(2024, 1, 1)
        assert bill.billing_period_end == date(2024, 1, 31)
        assert bill.billing_days == 31

    def test_dot_date_format_parsed(self):
        extraction = _make_extraction([
            _entity("service_period_start", "01.01.2024"),
            _entity("service_period_end", "31.01.2024"),
        ])
        bill = normalize_bill(extraction)
        assert bill.billing_period_start == date(2024, 1, 1)

    def test_inverted_dates_produce_warning(self):
        extraction = _make_extraction([
            _entity("service_period_start", "2024-02-01"),
            _entity("service_period_end", "2024-01-01"),
        ])
        bill = normalize_bill(extraction)
        assert bill.billing_period_start is None
        assert any("not after" in n for n in bill.extraction_notes)


class TestFloatParsing:
    def test_plain_number_parsed(self):
        extraction = _make_extraction([
            _entity("electricity_usage", "312.5"),
            _entity("total_amount", "87.40"),
        ])
        bill = normalize_bill(extraction)
        assert bill.electricity_import_kwh == 312.5
        assert bill.total_amount == 87.40

    def test_value_with_unit_text_parsed(self):
        extraction = _make_extraction([
            _entity("electricity_usage", "312.5 kWh"),
        ])
        bill = normalize_bill(extraction)
        assert bill.electricity_import_kwh == 312.5

    def test_european_decimal_comma_parsed(self):
        extraction = _make_extraction([
            _entity("total_amount", "312,50"),
        ])
        bill = normalize_bill(extraction)
        assert bill.total_amount == 312.50


class TestRateDerivation:
    def test_import_rate_from_energy_charge(self):
        extraction = _make_extraction([
            _entity("electricity_usage", "400.0"),
            _entity("electricity_amount", "200.0"),
        ])
        bill = normalize_bill(extraction)
        assert bill.import_rate_per_kwh == pytest.approx(0.5, rel=1e-4)

    def test_import_rate_fallback_to_total_amount(self):
        extraction = _make_extraction([
            _entity("electricity_usage", "400.0"),
            _entity("total_amount", "300.0"),
        ])
        bill = normalize_bill(extraction)
        assert bill.import_rate_per_kwh == pytest.approx(0.75, rel=1e-4)
        assert any("total_amount" in n for n in bill.extraction_notes)

    def test_no_rate_when_kwh_missing(self):
        extraction = _make_extraction([
            _entity("total_amount", "300.0"),
        ])
        bill = normalize_bill(extraction)
        assert bill.import_rate_per_kwh is None


class TestFallbackEntityNames:
    def test_vendor_name_maps_to_provider(self):
        extraction = _make_extraction([_entity("vendor_name", "Acme Power")])
        bill = normalize_bill(extraction)
        assert bill.provider_name == "Acme Power"

    def test_amount_due_maps_to_total_amount(self):
        extraction = _make_extraction([_entity("amount_due", "150.0")])
        bill = normalize_bill(extraction)
        assert bill.total_amount == 150.0
