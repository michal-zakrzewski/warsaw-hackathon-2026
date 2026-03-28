"""Normalizes BillExtractionResult entities into a structured NormalizedBill."""

from __future__ import annotations

import re
from datetime import date
from typing import Callable

from app.domain.bill_intelligence_models import BillEntity, BillExtractionResult, NormalizedBill

# ---------------------------------------------------------------------------
# Entity type → NormalizedBill field: ordered candidate names
# ---------------------------------------------------------------------------

_CANDIDATES: dict[str, list[str]] = {
    "provider_name":          ["supplier_name", "vendor_name", "company_name", "utility_provider", "utility name", "biller name"],
    "account_number":         ["account_number", "account_id", "contract_number", "account no", "account #"],
    "meter_number":           ["meter_number", "meter_id", "meter_serial", "meter no", "meter #", "meter reading id"],
    "customer_name":          ["customer_name", "recipient_name", "bill_to_name", "customer", "name"],
    "service_address":        ["service_address", "service_location", "property_address", "bill_to_address", "service site", "premises address"],
    "billing_period_start":   ["service_period_start", "service_start_date", "billing_period_start", "start_date", "period_start", "billing from", "service from", "period from", "from date"],
    "billing_period_end":     ["service_period_end", "service_end_date", "billing_period_end", "end_date", "period_end", "billing to", "service to", "period to", "to date"],
    "total_amount":           ["total_amount", "total_due", "amount_due", "balance_due", "payment_amount", "total charges", "amount to pay", "total bill", "please pay", "current charges"],
    "previous_balance":       ["previous_balance", "prior_balance", "carried_forward", "previous balance", "balance forward"],
    "electricity_import_kwh": ["electricity_usage", "electricity/total_usage", "energy_usage", "total_usage", "kwh_used", "active_energy_import", "electricity/usage", "total kwh", "kwh consumed", "energy consumed", "usage kwh", "electric usage", "electricity consumed"],
    "electricity_export_kwh": ["electricity_export", "electricity/export_usage", "export_kwh", "energy_export", "active_energy_export", "energy exported", "kwh exported", "feed-in kwh"],
    "energy_charge_amount":   ["electricity_amount", "electricity/amount", "energy_charge", "energy_cost", "electricity_charge", "energy charges", "electric charges", "supply charge"],
    "delivery_charge_amount": ["delivery_charge", "distribution_charge", "network_charge", "transmission_charge", "delivery charges", "distribution charges", "network charges"],
    "fixed_charge_amount":    ["fixed_charge", "standing_charge", "service_charge", "connection_charge", "daily supply charge", "basic service charge", "customer charge"],
    "taxes_amount":           ["vat_amount", "tax_amount", "taxes", "gst_amount", "vat", "tax", "gst", "sales tax"],
    "currency":               ["currency", "currency_code"],
}

# Candidate names that carry kWh values
_KWH_FIELDS = {"electricity_import_kwh", "electricity_export_kwh"}
# Candidate names that carry monetary amounts
_MONEY_FIELDS = {
    "total_amount", "previous_balance", "energy_charge_amount",
    "delivery_charge_amount", "fixed_charge_amount", "taxes_amount",
}


def normalize_bill(extraction: BillExtractionResult) -> NormalizedBill:
    """Build a NormalizedBill from a BillExtractionResult."""
    index = _build_entity_index(extraction.entities)
    notes: list[str] = list(extraction.warnings)

    # --- String fields ---
    provider_name   = _pick_text(index, _CANDIDATES["provider_name"])
    account_number  = _pick_text(index, _CANDIDATES["account_number"])
    meter_number    = _pick_text(index, _CANDIDATES["meter_number"])
    customer_name   = _pick_text(index, _CANDIDATES["customer_name"])
    service_address = _pick_text(index, _CANDIDATES["service_address"])
    currency        = _pick_text(index, _CANDIDATES["currency"])

    # --- Dates ---
    billing_period_start = _pick_date(index, _CANDIDATES["billing_period_start"], notes)
    billing_period_end   = _pick_date(index, _CANDIDATES["billing_period_end"], notes)

    billing_days: int | None = None
    if billing_period_start and billing_period_end:
        billing_days = (billing_period_end - billing_period_start).days + 1
        if billing_days <= 0:
            notes.append(
                f"billing_period_end ({billing_period_end}) is not after "
                f"billing_period_start ({billing_period_start}) — dates ignored"
            )
            billing_period_start = billing_period_end = None
            billing_days = None

    # --- Monetary amounts ---
    total_amount            = _pick_float(index, _CANDIDATES["total_amount"], notes)
    previous_balance        = _pick_float(index, _CANDIDATES["previous_balance"], notes)
    energy_charge_amount    = _pick_float(index, _CANDIDATES["energy_charge_amount"], notes)
    delivery_charge_amount  = _pick_float(index, _CANDIDATES["delivery_charge_amount"], notes)
    fixed_charge_amount     = _pick_float(index, _CANDIDATES["fixed_charge_amount"], notes)
    taxes_amount            = _pick_float(index, _CANDIDATES["taxes_amount"], notes)

    # --- Energy values ---
    electricity_import_kwh = _pick_float(index, _CANDIDATES["electricity_import_kwh"], notes)
    electricity_export_kwh = _pick_float(index, _CANDIDATES["electricity_export_kwh"], notes)

    # --- Derived rates ---
    import_rate_per_kwh: float | None = None
    if energy_charge_amount and electricity_import_kwh and electricity_import_kwh > 0:
        import_rate_per_kwh = round(energy_charge_amount / electricity_import_kwh, 6)
    elif total_amount and electricity_import_kwh and electricity_import_kwh > 0:
        import_rate_per_kwh = round(total_amount / electricity_import_kwh, 6)
        notes.append(
            "import_rate_per_kwh derived from total_amount / import_kwh "
            "(energy_charge_amount not available) — may include non-energy costs"
        )

    export_credit_per_kwh: float | None = None
    if electricity_export_kwh and electricity_export_kwh > 0:
        export_credit = _pick_float(index, ["electricity/export_credit", "export_credit", "feed_in_credit"], notes)
        if export_credit:
            export_credit_per_kwh = round(export_credit / electricity_export_kwh, 6)

    # Sanity check: total_amount should be > energy_charge if both present
    if total_amount and energy_charge_amount and energy_charge_amount > total_amount * 1.5:
        notes.append(
            f"energy_charge_amount ({energy_charge_amount}) exceeds 1.5× total_amount "
            f"({total_amount}) — possible extraction error"
        )

    return NormalizedBill(
        document_id=extraction.document_id,
        provider_name=provider_name,
        account_number=account_number,
        meter_number=meter_number,
        customer_name=customer_name,
        service_address=service_address,
        billing_period_start=billing_period_start,
        billing_period_end=billing_period_end,
        billing_days=billing_days,
        currency=currency,
        total_amount=total_amount,
        previous_balance=previous_balance,
        electricity_import_kwh=electricity_import_kwh,
        electricity_export_kwh=electricity_export_kwh,
        energy_charge_amount=energy_charge_amount,
        delivery_charge_amount=delivery_charge_amount,
        fixed_charge_amount=fixed_charge_amount,
        taxes_amount=taxes_amount,
        import_rate_per_kwh=import_rate_per_kwh,
        export_credit_per_kwh=export_credit_per_kwh,
        document_confidence=extraction.confidence,
        extraction_notes=notes,
        source_document_ids=[extraction.document_id],
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_entity_index(entities: list[BillEntity]) -> dict[str, list[BillEntity]]:
    index: dict[str, list[BillEntity]] = {}
    for entity in entities:
        index.setdefault(entity.type.lower(), []).append(entity)
    return index


def _pick_entity(index: dict[str, list[BillEntity]], candidates: list[str]) -> BillEntity | None:
    for name in candidates:
        hits = index.get(name.lower())
        if hits:
            # Prefer highest confidence
            return max(hits, key=lambda e: e.confidence or 0.0)
    return None


def _pick_text(index: dict[str, list[BillEntity]], candidates: list[str]) -> str | None:
    entity = _pick_entity(index, candidates)
    if entity is None:
        return None
    return entity.normalized_value or entity.mention_text or None


def _pick_date(
    index: dict[str, list[BillEntity]],
    candidates: list[str],
    notes: list[str],
) -> date | None:
    entity = _pick_entity(index, candidates)
    if entity is None:
        return None
    raw = entity.normalized_value or entity.mention_text
    if not raw:
        return None
    return _parse_date(raw, notes)


def _parse_date(raw: str, notes: list[str]) -> date | None:
    raw = raw.strip()
    # ISO format: YYYY-MM-DD
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", raw)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass
    # DD.MM.YYYY or DD/MM/YYYY
    m = re.match(r"^(\d{1,2})[./](\d{1,2})[./](\d{4})$", raw)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            pass
    # MM/DD/YYYY
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", raw)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(1)), int(m.group(2)))
        except ValueError:
            pass
    notes.append(f"Could not parse date value: '{raw}'")
    return None


def _pick_float(
    index: dict[str, list[BillEntity]],
    candidates: list[str],
    notes: list[str],
) -> float | None:
    entity = _pick_entity(index, candidates)
    if entity is None:
        return None
    raw = entity.normalized_value or entity.mention_text
    if not raw:
        return None
    return _parse_float(raw, notes)


def _parse_float(raw: str, notes: list[str]) -> float | None:
    # Strip currency symbols, unit text, thousand separators
    cleaned = re.sub(r"[^\d.,\-]", "", raw.strip())
    # Handle European decimal comma
    if re.search(r",\d{1,2}$", cleaned):
        cleaned = cleaned.replace(".", "").replace(",", ".")
    else:
        cleaned = cleaned.replace(",", "")
    try:
        value = float(cleaned)
        return round(value, 4) if value != 0 else None
    except ValueError:
        notes.append(f"Could not parse numeric value: '{raw}'")
        return None
