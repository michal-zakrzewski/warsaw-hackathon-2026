"""Quick integration test: send real fixture bills to Document AI and print results."""
from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# Add bill_intelligence to path
sys.path.insert(0, str(Path(__file__).parent / "bill_intelligence"))

from app.config.settings import get_settings
from app.clients.documentai_client import GoogleDocumentAIClient
from app.domain.bill_intelligence_models import BillDocumentInput
from app.services.bill_intelligence_agent import BillIntelligenceAgent
from app.domain.bill_intelligence_models import BillIntelligenceRequest

FIXTURES = Path(__file__).parent / "tests" / "fixtures"
FILES = [
    "demo_bill_04_commercial_q1.pdf",
    "demo_bill_05_commercial_q2.pdf",
    "demo_bill_06_commercial_q3.pdf",
]

MIME = "application/pdf"


def main():
    settings = get_settings()
    missing = settings.validate_for_real_client()
    if missing:
        print(f"ERROR: Missing env vars: {missing}")
        sys.exit(1)

    print(f"Project:    {settings.google_cloud_project}")
    print(f"Location:   {settings.documentai_location}")
    print(f"Processor:  {settings.documentai_primary_processor_id} ({settings.documentai_primary_processor_type})")
    print()

    client = GoogleDocumentAIClient(
        project_id=settings.google_cloud_project,
        location=settings.documentai_location,
        primary_processor_id=settings.documentai_primary_processor_id,
        primary_processor_type=settings.documentai_primary_processor_type,
    )

    documents = []
    for i, fname in enumerate(FILES, 1):
        fpath = FIXTURES / fname
        if not fpath.exists():
            print(f"SKIP (not found): {fname}")
            continue
        b64 = base64.b64encode(fpath.read_bytes()).decode()
        documents.append(BillDocumentInput(
            document_id=f"bill-{i:02d}",
            source_type="base64",
            base64_content=b64,
            mime_type=MIME,
            file_name=fname,
        ))
        print(f"Loaded: {fname} ({fpath.stat().st_size // 1024} KB)")

    print(f"\nSending {len(documents)} document(s) to Document AI...\n")

    agent = BillIntelligenceAgent(client)
    request = BillIntelligenceRequest(
        building_id="demo-building-001",
        documents=documents,
        annualization_mode="normalize_to_365",
        allow_fallback_processor=False,
    )
    result = agent.run(request)

    print("=" * 60)
    print("EXTRACTION RESULTS")
    print("=" * 60)
    for ext in result.extractions:
        status = "OK" if ext.success else "FAIL"
        print(f"  [{status}] {ext.document_id} — confidence={ext.confidence:.2f}, entities={len(ext.entities)}")
        if not ext.success or ext.warnings:
            for w in ext.warnings:
                print(f"         warning: {w}")

    print()
    print("=" * 60)
    print(f"RAW ENTITIES (bill-01 only)")
    print("=" * 60)
    for e in result.extractions[0].entities:
        print(f"  type={e.type!r:45s} mention={e.mention_text!r:30s} normalized={e.normalized_value!r}")

    print()
    print("=" * 60)
    print("NORMALIZED BILLS")
    print("=" * 60)
    for b in result.normalized_bills:
        print(f"  {b.document_id}")
        print(f"    Period:      {b.billing_period_start} → {b.billing_period_end} ({b.billing_days} days)")
        print(f"    Usage:       {b.electricity_import_kwh} kWh import, {b.electricity_export_kwh} kWh export")
        print(f"    Total bill:  {b.currency} {b.total_amount}")
        print(f"    Energy cost: {b.energy_charge_amount}")
        print(f"    Import rate: {b.import_rate_per_kwh} /kWh")
        print(f"    Export rate: {b.export_credit_per_kwh} /kWh")
        if b.extraction_notes:
            for note in b.extraction_notes:
                print(f"    NOTE: {note}")
        print()

    ps = result.portfolio_summary
    print("=" * 60)
    print("PORTFOLIO SUMMARY")
    print("=" * 60)
    print(f"  Valid bills:      {ps.valid_bill_count}")
    print(f"  Covered days:     {ps.covered_days}")
    print(f"  Confidence:       {ps.confidence:.2f}")
    if ps.warnings:
        for w in ps.warnings:
            print(f"  WARNING: {w}")

    di = result.derived_inputs
    print()
    print("=" * 60)
    print("DERIVED INPUTS (what shows in the UI table)")
    print("=" * 60)
    print(f"  annual_electricity_kwh:          {di.annual_electricity_kwh}")
    print(f"  annual_bill_cost:                {di.annual_bill_cost}")
    print(f"  electricity_import_rate_per_kwh: {di.electricity_import_rate_per_kwh}")
    print(f"  electricity_export_rate_per_kwh: {di.electricity_export_rate_per_kwh}")
    print(f"  confidence:                      {di.confidence:.2f}")
    if di.warnings:
        for w in di.warnings:
            print(f"  WARNING: {w}")


if __name__ == "__main__":
    main()
