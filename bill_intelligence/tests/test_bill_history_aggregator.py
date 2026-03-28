from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date

import pytest

from app.domain.bill_intelligence_models import NormalizedBill
from app.services.bill_history_aggregator import aggregate_bill_history


def _bill(
    doc_id: str,
    start: str,
    end: str,
    kwh: float | None = 300.0,
    amount: float | None = 90.0,
    energy_charge: float | None = 70.0,
    confidence: float = 0.90,
) -> NormalizedBill:
    s = date.fromisoformat(start)
    e = date.fromisoformat(end)
    return NormalizedBill(
        document_id=doc_id,
        billing_period_start=s,
        billing_period_end=e,
        billing_days=(e - s).days + 1,
        electricity_import_kwh=kwh,
        total_amount=amount,
        energy_charge_amount=energy_charge,
        document_confidence=confidence,
    )


class TestCoverageCalculation:
    def test_full_year_coverage(self):
        bills = [_bill(f"doc-{i:02d}", f"2024-{i:02d}-01", f"2024-{i:02d}-28") for i in range(1, 13)]
        summary = aggregate_bill_history(bills)
        assert summary.covered_days >= 330
        assert summary.valid_bill_count == 12

    def test_single_bill_coverage(self):
        bills = [_bill("doc-01", "2024-01-01", "2024-01-31")]
        summary = aggregate_bill_history(bills)
        assert summary.covered_days == 31
        assert summary.coverage_start == date(2024, 1, 1)
        assert summary.coverage_end == date(2024, 1, 31)


class TestAnnualization:
    def test_full_year_annualization(self):
        bills = [_bill(f"doc-{i:02d}", f"2024-{i:02d}-01", f"2024-{i:02d}-28", kwh=300.0, amount=90.0) for i in range(1, 13)]
        summary = aggregate_bill_history(bills)
        # ~336 days coverage → annualized ≈ 300*12 * (365/336)
        assert summary.annualized_import_kwh is not None
        assert summary.annualized_import_kwh > 3000

    def test_partial_year_still_annualizes_in_normalize_mode(self):
        bills = [_bill("doc-01", "2024-01-01", "2024-03-31", kwh=900.0, amount=270.0)]
        summary = aggregate_bill_history(bills, annualization_mode="normalize_to_365")
        assert summary.annualized_import_kwh is not None
        assert any("extrapolated" in w for w in summary.warnings)

    def test_partial_year_not_annualized_in_strict_mode(self):
        bills = [_bill("doc-01", "2024-01-01", "2024-03-31", kwh=900.0, amount=270.0)]
        summary = aggregate_bill_history(bills, annualization_mode="strict")
        assert summary.annualized_import_kwh is None


class TestBlendedRates:
    def test_blended_rate_from_energy_charges(self):
        bills = [
            _bill("doc-01", "2024-01-01", "2024-01-31", kwh=400.0, amount=100.0, energy_charge=80.0),
            _bill("doc-02", "2024-02-01", "2024-02-29", kwh=200.0, amount=60.0,  energy_charge=40.0),
        ]
        summary = aggregate_bill_history(bills)
        # sum(energy_charges) / sum(kwh) = 120 / 600 = 0.2
        assert summary.blended_import_rate_per_kwh == pytest.approx(0.2, rel=1e-4)

    def test_blended_rate_fallback_to_total_amount(self):
        bills = [_bill("doc-01", "2024-01-01", "2024-01-31", kwh=400.0, amount=120.0, energy_charge=None)]
        summary = aggregate_bill_history(bills)
        assert summary.blended_import_rate_per_kwh == pytest.approx(0.3, rel=1e-4)
        assert any("total_amount" in w for w in summary.warnings)


class TestGapsAndOverlaps:
    def test_gap_detected(self):
        bills = [
            _bill("doc-01", "2024-01-01", "2024-01-31"),
            _bill("doc-02", "2024-04-01", "2024-04-30"),  # 60-day gap
        ]
        summary = aggregate_bill_history(bills)
        assert any("gap" in w.lower() for w in summary.warnings)

    def test_overlap_detected(self):
        bills = [
            _bill("doc-01", "2024-01-01", "2024-02-15"),
            _bill("doc-02", "2024-02-01", "2024-02-29"),  # overlaps by 14 days
        ]
        summary = aggregate_bill_history(bills)
        assert any("overlap" in w.lower() for w in summary.warnings)

    def test_duplicate_document_id_deduplicated(self):
        bills = [
            _bill("doc-01", "2024-01-01", "2024-01-31"),
            _bill("doc-01", "2024-01-01", "2024-01-31"),  # duplicate
        ]
        summary = aggregate_bill_history(bills)
        assert summary.valid_bill_count == 1


class TestConfidence:
    def test_full_coverage_high_confidence(self):
        bills = [_bill(f"doc-{i:02d}", f"2024-{i:02d}-01", f"2024-{i:02d}-28") for i in range(1, 13)]
        summary = aggregate_bill_history(bills)
        assert summary.confidence >= 0.70

    def test_short_coverage_low_confidence(self):
        bills = [_bill("doc-01", "2024-01-01", "2024-01-31")]
        summary = aggregate_bill_history(bills)
        assert summary.confidence < 0.50

    def test_missing_kwh_reduces_confidence(self):
        bills = [_bill(f"doc-{i:02d}", f"2024-{i:02d}-01", f"2024-{i:02d}-28", kwh=None) for i in range(1, 13)]
        summary = aggregate_bill_history(bills)
        assert summary.confidence < 0.50


class TestMonthlyProfile:
    def test_profile_has_one_point_per_bill(self):
        bills = [
            _bill("doc-01", "2024-01-01", "2024-01-31", kwh=300.0),
            _bill("doc-02", "2024-02-01", "2024-02-29", kwh=280.0),
        ]
        summary = aggregate_bill_history(bills)
        assert len(summary.monthly_profile) == 2
        assert summary.monthly_profile[0].month == "2024-01"
        assert summary.monthly_profile[0].import_kwh == 300.0
