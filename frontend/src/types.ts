export interface IntakeFormData {
  businessName: string;
  businessType: string;
  address: string;
  latitude: string;
  longitude: string;
  annualEnergy: string;
  estimatedBudget: string;
  sustainabilityGoal: string;
  footprintArea: string;
}

export interface AgentInsight {
  icon: string;
  title: string;
  description: string;
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
  insights: AgentInsight[] | null;
}

export interface VoiceExtractedData {
  businessName: string | null;
  businessType: string | null;
  address: string | null;
  latitude: string | null;
  longitude: string | null;
  annualEnergy: string | null;
  estimatedBudget: string | null;
  sustainabilityGoal: string | null;
  additionalContext: string | null;
}

export interface AnalysisResult {
  agentText: string;
  formData: IntakeFormData;
  voiceContext?: string | null;
}
