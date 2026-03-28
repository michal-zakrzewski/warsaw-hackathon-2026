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

export interface AnalysisResult {
  agentText: string;
  formData: IntakeFormData;
}
