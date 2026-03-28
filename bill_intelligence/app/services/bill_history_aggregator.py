"""Aggregates a list of NormalizedBills into a BillPortfolioSummary."""

from __future__ import annotations

from datetime import date, timedelta

from app.domain.bill_intelligence_models import (
    BillPortfolioSummary,
    MonthlyConsumptionPoint,
    NormalizedBill,
)

_GAP_THRESHOLD_DAYS = 40
_MIN_DAYS_FOR_FULL_CONFIDENCE = 330
_MIN_DAYS_FOR_MEDIUM_CONFIDENCE = 180


def aggregate_bill_history(
    bills: list[NormalizedBill],
    annualization_mode: str = "normalize_to_365",
) -> BillPortfolioSummary:
    warnings: list[str] = []
    provenance: list[dict] = []

    valid_bills = _filter_valid(bills, warnings)

    if not valid_bills:
        return BillPortfolioSummary(
            document_count=len(bills),
            valid_bill_count=0,
            covered_days=0,
            confidence=0.0,
            warnings=warnings + ["No valid bills with billing period dates found"],
        )

    valid_bills = _sort_and_deduplicate(valid_bills, warnings)
    coverage_start, coverage_end, covered_days = _measure_coverage(valid_bills)
    _check_gaps(valid_bills, warnings)
    _check_overlaps(valid_bills, warnings)

    # --- Sums ---
    total_import_kwh   = _sum_or_none([b.electricity_import_kwh for b in valid_bills])
    total_export_kwh   = _sum_or_none([b.electricity_export_kwh for b in valid_bills])
    total_cost         = _sum_or_none([b.total_amount for b in valid_bills])
    total_energy_cost  = _sum_or_none([b.energy_charge_amount for b in valid_bills])

    # --- Annualization ---
    annualized_import_kwh:  float | None = None
    annualized_export_kwh:  float | None = None
    annualized_bill_cost:   float | None = None

    can_annualize = covered_days >= 300 or annualization_mode == "normalize_to_365"

    if can_annualize and covered_days > 0:
        factor = 365.0 / covered_days
        if total_import_kwh is not None:
            annualized_import_kwh = round(total_import_kwh * factor, 1)
        if total_export_kwh is not None:
            annualized_export_kwh = round(total_export_kwh * factor, 1)
        if total_cost is not None:
            annualized_bill_cost = round(total_cost * factor, 2)

        if covered_days < 300:
            warnings.append(
                f"Coverage is only {covered_days} days — annualized values are extrapolated "
                f"(factor {factor:.2f}×); confidence is reduced"
            )

    # --- Blended rates ---
    blended_import_rate_per_kwh   = _blended_import_rate(valid_bills, total_energy_cost, total_import_kwh, warnings)
    blended_export_credit_per_kwh = _blended_export_credit(valid_bills, warnings)

    # --- Average monthly bill ---
    average_monthly_bill: float | None = None
    if total_cost is not None and covered_days > 0:
        average_monthly_bill = round(total_cost / (covered_days / 30.44), 2)

    # --- Monthly profile ---
    monthly_profile = _build_monthly_profile(valid_bills)

    # --- Confidence ---
    confidence = _calculate_confidence(
        covered_days=covered_days,
        valid_bill_count=len(valid_bills),
        has_gaps=any("gap" in w.lower() for w in warnings),
        missing_kwh_count=sum(1 for b in valid_bills if b.electricity_import_kwh is None),
        missing_amount_count=sum(1 for b in valid_bills if b.total_amount is None),
        has_overlaps=any("overlap" in w.lower() for w in warnings),
    )

    # --- Provenance ---
    for bill in valid_bills:
        provenance.append({
            "document_id": bill.document_id,
            "period": f"{bill.billing_period_start} – {bill.billing_period_end}",
            "import_kwh": bill.electricity_import_kwh,
            "total_amount": bill.total_amount,
            "confidence": bill.document_confidence,
        })

    return BillPortfolioSummary(
        document_count=len(bills),
        valid_bill_count=len(valid_bills),
        coverage_start=coverage_start,
        coverage_end=coverage_end,
        covered_days=covered_days,
        annualized_import_kwh=annualized_import_kwh,
        annualized_export_kwh=annualized_export_kwh,
        annualized_bill_cost=annualized_bill_cost,
        blended_import_rate_per_kwh=blended_import_rate_per_kwh,
        blended_export_credit_per_kwh=blended_export_credit_per_kwh,
        average_monthly_bill=average_monthly_bill,
        monthly_profile=monthly_profile,
        confidence=confidence,
        warnings=warnings,
        provenance=provenance,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _filter_valid(bills: list[NormalizedBill], warnings: list[str]) -> list[NormalizedBill]:
    valid: list[NormalizedBill] = []
    for bill in bills:
        if bill.billing_period_start and bill.billing_period_end:
            valid.append(bill)
        else:
            warnings.append(
                f"Document {bill.document_id} has no billing period dates — excluded from aggregation"
            )
    return valid


def _sort_and_deduplicate(
    bills: list[NormalizedBill], warnings: list[str]
) -> list[NormalizedBill]:
    sorted_bills = sorted(bills, key=lambda b: b.billing_period_start)  # type: ignore[arg-type]
    seen: set[str] = set()
    unique: list[NormalizedBill] = []
    for bill in sorted_bills:
        if bill.document_id in seen:
            warnings.append(f"Duplicate document_id '{bill.document_id}' — skipping second occurrence")
            continue
        seen.add(bill.document_id)
        unique.append(bill)
    return unique


def _measure_coverage(bills: list[NormalizedBill]) -> tuple[date, date, int]:
    starts = [b.billing_period_start for b in bills if b.billing_period_start]
    ends   = [b.billing_period_end   for b in bills if b.billing_period_end]
    coverage_start: date = min(starts)  # type: ignore[type-var]
    coverage_end:   date = max(ends)    # type: ignore[type-var]
    covered_days = (coverage_end - coverage_start).days + 1
    return coverage_start, coverage_end, covered_days


def _check_gaps(bills: list[NormalizedBill], warnings: list[str]) -> None:
    for i in range(1, len(bills)):
        prev_end   = bills[i - 1].billing_period_end
        curr_start = bills[i].billing_period_start
        if prev_end and curr_start:
            gap = (curr_start - prev_end).days - 1
            if gap > _GAP_THRESHOLD_DAYS:
                warnings.append(
                    f"Gap of {gap} days between {prev_end} and {curr_start} "
                    f"({bills[i-1].document_id} → {bills[i].document_id})"
                )


def _check_overlaps(bills: list[NormalizedBill], warnings: list[str]) -> None:
    for i in range(1, len(bills)):
        prev_end   = bills[i - 1].billing_period_end
        curr_start = bills[i].billing_period_start
        if prev_end and curr_start and curr_start < prev_end:
            overlap = (prev_end - curr_start).days
            warnings.append(
                f"Overlap of {overlap} days between {bills[i-1].document_id} "
                f"(ends {prev_end}) and {bills[i].document_id} (starts {curr_start})"
            )


def _sum_or_none(values: list[float | None]) -> float | None:
    actual = [v for v in values if v is not None]
    if not actual:
        return None
    return round(sum(actual), 4)


def _blended_import_rate(
    bills: list[NormalizedBill],
    total_energy_cost: float | None,
    total_import_kwh: float | None,
    warnings: list[str],
) -> float | None:
    if total_import_kwh is None or total_import_kwh <= 0:
        return None
    if total_energy_cost is not None and total_energy_cost > 0:
        return round(total_energy_cost / total_import_kwh, 6)
    # Fallback: use total_amount (includes delivery, taxes, etc.)
    total_cost = _sum_or_none([b.total_amount for b in bills])
    if total_cost is not None and total_cost > 0:
        warnings.append(
            "blended_import_rate_per_kwh computed from total_amount / import_kwh "
            "because energy_charge_amount was not available for all bills — "
            "rate includes non-energy costs (delivery, taxes)"
        )
        return round(total_cost / total_import_kwh, 6)
    return None


def _blended_export_credit(
    bills: list[NormalizedBill], warnings: list[str]
) -> float | None:
    export_totals = [b.electricity_export_kwh for b in bills if b.electricity_export_kwh]
    credit_rates  = [b.export_credit_per_kwh  for b in bills if b.export_credit_per_kwh]
    if not export_totals or not credit_rates:
        return None
    if len(credit_rates) < len(export_totals) // 2:
        warnings.append(
            "export_credit_per_kwh available for fewer than half of export bills — "
            "blended export credit may be unreliable"
        )
    return round(sum(credit_rates) / len(credit_rates), 6)


def _build_monthly_profile(bills: list[NormalizedBill]) -> list[MonthlyConsumptionPoint]:
    """Assigns each bill to the month of its billing_period_end (simple method).

    Note: each bill is assigned entirely to the end month.
    For higher accuracy, bills should be prorated by day across months.
    """
    monthly: dict[str, MonthlyConsumptionPoint] = {}
    for bill in bills:
        if not bill.billing_period_end:
            continue
        key = bill.billing_period_end.strftime("%Y-%m")
        if key not in monthly:
            monthly[key] = MonthlyConsumptionPoint(month=key)
        point = monthly[key]
        if bill.electricity_import_kwh is not None:
            point.import_kwh = (point.import_kwh or 0.0) + bill.electricity_import_kwh
        if bill.electricity_export_kwh is not None:
            point.export_kwh = (point.export_kwh or 0.0) + bill.electricity_export_kwh
        if bill.total_amount is not None:
            point.total_amount = (point.total_amount or 0.0) + bill.total_amount

    return [monthly[k] for k in sorted(monthly.keys())]


def _calculate_confidence(
    covered_days: int,
    valid_bill_count: int,
    has_gaps: bool,
    missing_kwh_count: int,
    missing_amount_count: int,
    has_overlaps: bool,
) -> float:
    if covered_days >= _MIN_DAYS_FOR_FULL_CONFIDENCE:
        base = 0.90
    elif covered_days >= _MIN_DAYS_FOR_MEDIUM_CONFIDENCE:
        base = 0.65
    elif covered_days >= 90:
        base = 0.40
    else:
        base = 0.20

    if has_gaps:
        base *= 0.85
    if has_overlaps:
        base *= 0.80

    if valid_bill_count > 0:
        kwh_ratio    = 1.0 - missing_kwh_count    / valid_bill_count
        amount_ratio = 1.0 - missing_amount_count / valid_bill_count
        completeness = kwh_ratio * 0.6 + amount_ratio * 0.4
        base *= completeness

    return round(min(1.0, max(0.0, base)), 3)
