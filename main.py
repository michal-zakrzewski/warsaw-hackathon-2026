"""Example usage of the Google Solar API connector."""

import json
import os
from pathlib import Path

from dotenv import load_dotenv

from solar_client import GoogleSolarClient

load_dotenv(Path(__file__).parent / ".env")
API_KEY = os.environ.get("GOOGLE_SOLAR_API_KEY", "")


def main() -> None:
    if not API_KEY:
        print("Set GOOGLE_SOLAR_API_KEY in .env first.")
        return

    client = GoogleSolarClient(api_key=API_KEY)

    # Show current monthly usage before making any calls
    print("--- Monthly usage ---")
    client.usage_status()
    print()

    # Option A: query by address (requires Geocoding API enabled)
    lat, lng = client.geocode("1600 Amphitheatre Pkwy, Mountain View, CA")
    print(f"Geocoded to: {lat}, {lng}\n")

    # Option B: pass coordinates directly
    # lat, lng = 37.4450, -122.1390

    # 1) Building Insights — structured solar potential data
    building = client.find_closest_building(lat, lng)
    sp = building.solar_potential

    print(f"Building: {building.name}")
    print(f"Imagery quality: {building.imagery_quality}")
    if sp:
        print(f"Max panels: {sp.max_array_panels_count}")
        print(f"Max sunshine hours/year: {sp.max_sunshine_hours_per_year}")
        print(f"Max array area: {sp.max_array_area_meters2} m²")
        print(f"Panel capacity: {sp.panel_capacity_watts} W")
        print(f"Carbon offset: {sp.carbon_offset_factor_kg_per_mwh} kg/MWh")
        print(f"Roof segments: {len(sp.roof_segment_stats)}")
        print(f"Panel configurations: {len(sp.solar_panel_configs)}")
        print(f"Financial analyses: {len(sp.financial_analyses)}")

    # 2) Data Layers — GeoTIFF raster URLs for GIS analysis
    layers = client.get_data_layers(lat, lng, radius_meters=100)
    print(f"\nDSM URL: {layers.dsm_url[:80]}...")
    print(f"Annual flux URL: {layers.annual_flux_url[:80]}...")
    print(f"Monthly flux URL: {layers.monthly_flux_url[:80]}...")
    print(f"Hourly shade files: {len(layers.hourly_shade_urls)}")

    # Download a raster (uncomment to use):
    # client.download_geotiff(layers.annual_flux_url, "data/annual_flux.tif")

    # Dump full BuildingInsights as JSON for inspection
    print("\n--- BuildingInsights (truncated) ---")
    print(json.dumps(building.model_dump(by_alias=True), indent=2, default=str)[:2000])


if __name__ == "__main__":
    main()
