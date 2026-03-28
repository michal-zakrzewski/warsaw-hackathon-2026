export interface IntakeFormData {
  businessName: string;
  businessType: string;
  address: string;
  latitude: string;
  longitude: string;
  annualEnergy: string;
  estimatedBudget: string;
  sustainabilityGoal: string;
  // Building details (optional, Step 2)
  buildingType: string;
  roofType: string;
  wallMaterial: string;
  windowType: string;
  footprintArea: string;
  floorsCount: string;
  floorHeight: string;
}

export interface AgentMetrics {
  heat_loss_kw: number | null;
  heat_loss_range: string | null;
  dominant_loss_source: string | null;
  solar_panels: number | null;
  solar_output_kwh: number | null;
  co2_reduction_tons: number | null;
  estimated_payback_years: number | null;
  annual_savings_usd: number | null;
  recommended_project: string | null;
  geometry_confidence: number | null;
  site_stability_score: number | null;
}

export interface AnalysisResult {
  agentText: string;
  formData: IntakeFormData;
}
