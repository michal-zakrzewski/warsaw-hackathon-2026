const BILL_API_BASE = "/bill-api";

export interface DerivedComparisonInputs {
  annual_electricity_kwh: number | null;
  annual_bill_cost: number | null;
  electricity_import_rate_per_kwh: number | null;
  electricity_export_rate_per_kwh: number | null;
  confidence: number;
  warnings: string[];
  provenance: Record<string, unknown>[];
}

export interface BillIntelligenceResult {
  building_id: string;
  derived_inputs: DerivedComparisonInputs;
  portfolio_summary: {
    valid_bill_count: number;
    covered_days: number;
    confidence: number;
    warnings: string[];
  };
}

async function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      // Strip the "data:...;base64," prefix
      resolve(result.split(",")[1]);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

export async function processBills(
  buildingId: string,
  files: File[]
): Promise<BillIntelligenceResult> {
  const documents = await Promise.all(
    files.map(async (file, i) => ({
      document_id: `bill-${i + 1}`,
      source_type: "base64",
      base64_content: await fileToBase64(file),
      mime_type: file.type || "application/pdf",
      file_name: file.name,
    }))
  );

  const res = await fetch(`${BILL_API_BASE}/bill-intelligence/process`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      building_id: buildingId,
      annualization_mode: "normalize_to_365",
      allow_fallback_processor: true,
      documents,
    }),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Bill Intelligence API error ${res.status}: ${err}`);
  }

  return res.json();
}
