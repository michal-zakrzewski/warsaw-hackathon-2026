Python connector for the **Google Maps Platform Solar API** — programmatically fetch solar potential data for any building (the same data behind [Project Sunroof](https://sunroof.withgoogle.com)), without touching the UI.

Stays within free-tier limits by default and raises an error before any call that would incur a charge.

## What it returns

For any address or GPS coordinates:

- **Rooftop solar potential** — max panel count, max area, sunshine hours/year
- **Roof segments** — pitch, azimuth, and irradiance per segment
- **Panel configurations** — N panels → kWh/year
- **Financial analysis** — estimated savings, payback period, leasing vs. purchase
- **GeoTIFF rasters** — DSM (3D surface model), annual/monthly solar flux, hourly shade

## Project structure

```
solar_client/
├── client.py         — GoogleSolarClient: find_closest_building, get_data_layers, download_geotiff, geocode, usage_status
├── models.py         — Pydantic models: BuildingInsights, SolarPotential, DataLayers, ...
├── usage_tracker.py  — Free-tier usage tracking (persisted to .usage.json)
└── exceptions.py     — SolarApiError, FreeTierExceeded
main.py               — Usage example
.env                  — API key (git-ignored)
requirements.txt
```

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure the API key

You need a Google Maps Platform key with the following APIs enabled:
- **Solar API** (required)
- **Geocoding API** (optional — only needed for address-to-coordinates lookup)

Create a key in [Google Cloud Console](https://console.cloud.google.com/) → APIs & Services → Credentials.

Add it to `.env`:

```
GOOGLE_SOLAR_API_KEY=your_key_here
```

### 3. Run the example

```bash
python main.py
```

## Usage

```python
from dotenv import load_dotenv
import os
from solar_client import GoogleSolarClient

load_dotenv()
client = GoogleSolarClient(api_key=os.environ["GOOGLE_SOLAR_API_KEY"])
```

### Query by address

```python
lat, lng = client.geocode("1600 Amphitheatre Pkwy, Mountain View, CA")
building = client.find_closest_building(lat, lng)
```

### Query by coordinates

```python
building = client.find_closest_building(37.4450, -122.1390)
```

### Read solar data

```python
sp = building.solar_potential

sp.max_array_panels_count           # int   — maximum number of panels
sp.max_sunshine_hours_per_year      # float — sunshine hours per year
sp.max_array_area_meters2           # float — maximum installation area [m²]
sp.panel_capacity_watts             # float — power per panel [W]
sp.panel_lifetime_years             # int   — panel lifetime [years]
sp.carbon_offset_factor_kg_per_mwh  # float — CO₂ offset [kg/MWh]

sp.roof_segment_stats               # list of roof segments
sp.solar_panel_configs              # list of configurations (N panels → kWh/year)
sp.financial_analyses               # list of financial analyses
```

### Panel configurations

```python
for config in sp.solar_panel_configs:
    print(config.panels_count, "panels →", config.yearly_energy_dc_kwh, "kWh/year")
```

### GeoTIFF rasters (for GIS analysis)

```python
layers = client.get_data_layers(lat, lng, radius_meters=100)

layers.dsm_url           # Digital Surface Model (terrain elevation)
layers.rgb_url           # aerial/satellite RGB image
layers.mask_url          # rooftop mask
layers.annual_flux_url   # annual solar flux [kWh/kW/year]
layers.monthly_flux_url  # monthly flux (12 bands)
layers.hourly_shade_urls # 12 files × 24 hourly shade bands

# Download a raster locally
client.download_geotiff(layers.annual_flux_url, "data/annual_flux.tif")
```

Use `rasterio` or `xarray` to read GeoTIFFs. Note: most of these files appear "empty" in standard image viewers — they contain analytical data for GIS tools, not photographs.

### Check usage

```python
client.usage_status()
# building_insights: 3/10000 used (9997 remaining) — 2026-03
# data_layers:       1/1000 used (999 remaining) — 2026-03
```

## Free-tier limits

| Endpoint | Free/month | Price after |
|----------|-----------|-------------|
| `buildingInsights` | 10,000 calls | $10 / 1,000 |
| `dataLayers` | 1,000 calls | $75 / 1,000 |

The client blocks any call that would exceed the free limit and raises `FreeTierExceeded`. To allow paid usage explicitly:

```python
client = GoogleSolarClient(api_key=..., allow_paid=True)
```

Usage counts are stored in `.usage.json` (git-ignored) and reset automatically at the start of each calendar month.

## Data models

| Model | Description |
|-------|-------------|
| `BuildingInsights` | Top-level response — location, imagery quality, `solar_potential` |
| `SolarPotential` | Solar potential — panels, energy, segments, configs, financials |
| `RoofSegmentStats` | Single roof segment — pitch, azimuth, irradiance |
| `SolarPanelConfig` | Configuration of N panels with annual kWh output |
| `FinancialAnalysis` | Financial analysis for a given panel configuration |
| `DataLayers` | URLs to 17 GeoTIFF rasters for an area |

## Limitations

- **Coverage**: Data is available mainly for the US, Japan, Germany, Australia, India, and select European cities. The API returns `404` for locations without data.
- **EEA (EU)**: From 8 July 2025, keys billed in the EEA will not return `postalCode`, `administrativeArea`, or `regionCode`. These fields are `Optional` in the models.
- **GeoTIFF URLs**: Valid for only a few hours after generation — download promptly.
- **Geocoding**: Requires the Geocoding API enabled on the same key. Alternatively, pass coordinates directly.
