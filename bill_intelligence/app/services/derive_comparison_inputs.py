"""Derives final comparison inputs from BillPortfolioSummary."""

from __future__ import annotations

from app.domain.bill_intelligence_models import BillPortfolioSummary, DerivedComparisonInputs


def derive_comparison_inputs(summary: BillPortfolioSummary) -> DerivedComparisonInputs:
    """Map portfolio summary to the flat structure consumed by comparison modules."""
    warnings: list[str] = list(summary.warnings)
    provenance: list[dict] = []

    annual_electricity_kwh      = summary.annualized_import_kwh
    annual_bill_cost            = summary.annualized_bill_cost
    electricity_import_rate     = summary.blended_import_rate_per_kwh
    electricity_export_rate     = summary.blended_export_credit_per_kwh

    # --- Field-level provenance ---
    if annual_electricity_kwh is not None:
        provenance.append({
            "field": "annual_electricity_kwh",
            "value": annual_electricity_kwh,
            "source": "annualized_import_kwh from portfolio aggregation",
            "covered_days": summary.covered_days,
            "bill_count": summary.valid_bill_count,
        })
    else:
        warnings.append("annual_electricity_kwh could not be derived — import kWh missing from bills")

    if annual_bill_cost is not None:
        provenance.append({
            "field": "annual_bill_cost",
            "value": annual_bill_cost,
            "source": "annualized total_amount from portfolio aggregation",
            "covered_days": summary.covered_days,
            "bill_count": summary.valid_bill_count,
        })
    else:
        warnings.append("annual_bill_cost could not be derived — total_amount missing from bills")

    if electricity_import_rate is not None:
        provenance.append({
            "field": "electricity_import_rate_per_kwh",
            "value": electricity_import_rate,
            "source": "blended_import_rate_per_kwh: sum(energy_charges) / sum(import_kwh)",
        })
    else:
        warnings.append("electricity_import_rate_per_kwh could not be derived")

    if electricity_export_rate is not None:
        provenance.append({
            "field": "electricity_export_rate_per_kwh",
            "value": electricity_export_rate,
            "source": "blended_export_credit_per_kwh from prosumer bills",
        })

    return DerivedComparisonInputs(
        annual_electricity_kwh=annual_electricity_kwh,
        annual_bill_cost=annual_bill_cost,
        electricity_import_rate_per_kwh=electricity_import_rate,
        electricity_export_rate_per_kwh=electricity_export_rate,
        confidence=summary.confidence,
        warnings=warnings,
        provenance=provenance,
    )
