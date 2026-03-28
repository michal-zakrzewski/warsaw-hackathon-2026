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

export interface AnalysisResult {
  agentText: string;
  formData: IntakeFormData;
}
