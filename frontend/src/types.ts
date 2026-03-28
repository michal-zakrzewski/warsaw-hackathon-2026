export interface IntakeFormData {
  businessName: string;
  businessType: string;
  address: string;
  latitude: string;
  longitude: string;
  annualEnergy: string;
  estimatedBudget: string;
  sustainabilityGoal: string;
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
