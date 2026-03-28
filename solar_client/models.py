from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


# ---------- primitives ----------

class LatLng(BaseModel):
    latitude: float
    longitude: float


class Date(BaseModel):
    year: int
    month: int
    day: int


class Money(BaseModel):
    currency_code: str = Field(alias="currencyCode", default="")
    units: str = ""
    nanos: int = 0


# ---------- solar potential ----------

class SunshineStats(BaseModel):
    area_meters2: float = Field(alias="areaMeters2", default=0)
    sunshine_quantiles: list[float] = Field(alias="sunshineQuantiles", default_factory=list)
    ground_area_meters2: float = Field(alias="groundAreaMeters2", default=0)


class RoofSegmentStats(BaseModel):
    pitch_degrees: float = Field(alias="pitchDegrees", default=0)
    azimuth_degrees: float = Field(alias="azimuthDegrees", default=0)
    stats: Optional[SunshineStats] = None
    center: Optional[LatLng] = None
    bounding_box: Optional[dict] = Field(alias="boundingBox", default=None)
    plane_height_at_center_meters: float = Field(alias="planeHeightAtCenterMeters", default=0)


class SolarPanel(BaseModel):
    center: Optional[LatLng] = None
    orientation: str = ""
    segment_index: Optional[int] = Field(alias="segmentIndex", default=None)
    yearly_energy_dc_kwh: float = Field(alias="yearlyEnergyDcKwh", default=0)


class RoofSegmentSummary(BaseModel):
    panels_count: int = Field(alias="panelsCount", default=0)
    yearly_energy_dc_kwh: float = Field(alias="yearlyEnergyDcKwh", default=0)
    segment_index: Optional[int] = Field(alias="segmentIndex", default=None)


class SolarPanelConfig(BaseModel):
    panels_count: int = Field(alias="panelsCount", default=0)
    yearly_energy_dc_kwh: float = Field(alias="yearlyEnergyDcKwh", default=0)
    roof_segment_summaries: list[RoofSegmentSummary] = Field(
        alias="roofSegmentSummaries", default_factory=list
    )


class CashPurchaseSavings(BaseModel):
    out_of_pocket_cost: Optional[Money] = Field(alias="outOfPocketCost", default=None)
    upfront_cost: Optional[Money] = Field(alias="upfrontCost", default=None)
    rebate_value: Optional[Money] = Field(alias="rebateValue", default=None)
    payback_years: Optional[float] = Field(alias="paybackYears", default=None)
    savings: Optional[Money] = None


class FinancedPurchaseSavings(BaseModel):
    annual_loan_payment: Optional[Money] = Field(alias="annualLoanPayment", default=None)
    rebate_value: Optional[Money] = Field(alias="rebateValue", default=None)
    loan_interest_rate: Optional[float] = Field(alias="loanInterestRate", default=None)
    savings: Optional[Money] = None


class LeasingSavings(BaseModel):
    leases_allowed: bool = Field(alias="leasesAllowed", default=False)
    leases_supported: bool = Field(alias="leasesSupported", default=False)
    annual_leasing_cost: Optional[Money] = Field(alias="annualLeasingCost", default=None)
    savings: Optional[Money] = None


class FinancialDetails(BaseModel):
    initial_ac_kwh_per_year: float = Field(alias="initialAcKwhPerYear", default=0)
    remaining_lifetime_utility_bill: Optional[Money] = Field(
        alias="remainingLifetimeUtilityBill", default=None
    )
    federal_incentive: Optional[Money] = Field(alias="federalIncentive", default=None)
    state_incentive: Optional[Money] = Field(alias="stateIncentive", default=None)
    utility_incentive: Optional[Money] = Field(alias="utilityIncentive", default=None)
    lifetime_srec_total: Optional[Money] = Field(alias="lifetimeSrecTotal", default=None)
    cost_of_electricity_without_solar: Optional[Money] = Field(
        alias="costOfElectricityWithoutSolar", default=None
    )
    net_metering_allowed: bool = Field(alias="netMeteringAllowed", default=False)
    solar_percentage: Optional[float] = Field(alias="solarPercentage", default=None)
    percentage_exported_to_grid: Optional[float] = Field(
        alias="percentageExportedToGrid", default=None
    )
    cash_purchase_savings: Optional[CashPurchaseSavings] = Field(
        alias="cashPurchaseSavings", default=None
    )
    financed_purchase_savings: Optional[FinancedPurchaseSavings] = Field(
        alias="financedPurchaseSavings", default=None
    )
    leasing_savings: Optional[LeasingSavings] = Field(alias="leasingSavings", default=None)


class FinancialAnalysis(BaseModel):
    monthly_bill: Optional[Money] = Field(alias="monthlyBill", default=None)
    panel_config_index: int = Field(alias="panelConfigIndex", default=0)
    financial_details: Optional[FinancialDetails] = Field(alias="financialDetails", default=None)


class SolarPotential(BaseModel):
    max_array_panels_count: int = Field(alias="maxArrayPanelsCount", default=0)
    panel_capacity_watts: float = Field(alias="panelCapacityWatts", default=0)
    panel_height_meters: float = Field(alias="panelHeightMeters", default=0)
    panel_width_meters: float = Field(alias="panelWidthMeters", default=0)
    panel_lifetime_years: int = Field(alias="panelLifetimeYears", default=0)
    max_array_area_meters2: float = Field(alias="maxArrayAreaMeters2", default=0)
    max_sunshine_hours_per_year: float = Field(alias="maxSunshineHoursPerYear", default=0)
    carbon_offset_factor_kg_per_mwh: float = Field(alias="carbonOffsetFactorKgPerMwh", default=0)
    whole_roof_stats: Optional[SunshineStats] = Field(alias="wholeRoofStats", default=None)
    building_stats: Optional[SunshineStats] = Field(alias="buildingStats", default=None)
    roof_segment_stats: list[RoofSegmentStats] = Field(
        alias="roofSegmentStats", default_factory=list
    )
    solar_panels: list[SolarPanel] = Field(alias="solarPanels", default_factory=list)
    solar_panel_configs: list[SolarPanelConfig] = Field(
        alias="solarPanelConfigs", default_factory=list
    )
    financial_analyses: list[FinancialAnalysis] = Field(
        alias="financialAnalyses", default_factory=list
    )


# ---------- building insights ----------

class BuildingInsights(BaseModel):
    name: str = ""
    center: Optional[LatLng] = None
    bounding_box: Optional[dict] = Field(alias="boundingBox", default=None)
    imagery_date: Optional[Date] = Field(alias="imageryDate", default=None)
    imagery_processed_date: Optional[Date] = Field(alias="imageryProcessedDate", default=None)
    postal_code: Optional[str] = Field(alias="postalCode", default=None)
    administrative_area: Optional[str] = Field(alias="administrativeArea", default=None)
    statistical_area: Optional[str] = Field(alias="statisticalArea", default=None)
    region_code: Optional[str] = Field(alias="regionCode", default=None)
    solar_potential: Optional[SolarPotential] = Field(alias="solarPotential", default=None)
    imagery_quality: str = Field(alias="imageryQuality", default="")

    model_config = {"populate_by_name": True}


# ---------- data layers ----------

class DataLayers(BaseModel):
    imagery_date: Optional[Date] = Field(alias="imageryDate", default=None)
    imagery_processed_date: Optional[Date] = Field(alias="imageryProcessedDate", default=None)
    dsm_url: str = Field(alias="dsmUrl", default="")
    rgb_url: str = Field(alias="rgbUrl", default="")
    mask_url: str = Field(alias="maskUrl", default="")
    annual_flux_url: str = Field(alias="annualFluxUrl", default="")
    monthly_flux_url: str = Field(alias="monthlyFluxUrl", default="")
    hourly_shade_urls: list[str] = Field(alias="hourlyShadeUrls", default_factory=list)
    imagery_quality: str = Field(alias="imageryQuality", default="")

    model_config = {"populate_by_name": True}
