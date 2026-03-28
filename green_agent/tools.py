"""ADK tool functions wrapping satellite_embedding and solar_client connectors."""

from __future__ import annotations

import os

_ee_initialized = False
_solar_client_instance = None


def _ensure_ee() -> None:
    global _ee_initialized
    if _ee_initialized:
        return
    from satellite_embedding.connector import init as ee_init

    ee_init()
    _ee_initialized = True


def _get_solar_client():
    global _solar_client_instance
    if _solar_client_instance is not None:
        return _solar_client_instance
    from solar_client import GoogleSolarClient

    key = os.environ.get("GOOGLE_SOLAR_API_KEY", "")
    if not key:
        raise ValueError(
            "Set GOOGLE_SOLAR_API_KEY to use solar tools."
        )
    _solar_client_instance = GoogleSolarClient(api_key=key)
    return _solar_client_instance


# ---------------------------------------------------------------------------
# Satellite embedding tools
# ---------------------------------------------------------------------------


def get_site_embedding(longitude: float, latitude: float, year: int) -> dict:
    """Get the 64-dimensional satellite embedding vector at a location for a given year.

    Use this to understand the geospatial characteristics of a site.
    Each value represents one axis of a learned embedding space derived from
    multi-source satellite observations (optical, radar, LiDAR).

    Args:
        longitude: WGS84 longitude of the site.
        latitude: WGS84 latitude of the site.
        year: Calendar year (2017 onward).

    Returns:
        A dict mapping band names (A00–A63) to float values.
    """
    _ensure_ee()
    from satellite_embedding.connector import sample_point

    return sample_point(longitude, latitude, year)


def compare_site_years(
    longitude: float,
    latitude: float,
    year_a: int,
    year_b: int,
) -> dict:
    """Compare satellite embeddings at the same location across two years.

    Returns a similarity score (dot product of unit-length embedding vectors).
    A score near 1.0 means the land-use context is very stable between the two
    years — good for long-term investment. Lower values indicate significant
    environmental or land-use change.

    Args:
        longitude: WGS84 longitude.
        latitude: WGS84 latitude.
        year_a: First calendar year.
        year_b: Second calendar year.

    Returns:
        Dict with keys: similarity (float), year_a (int), year_b (int).
    """
    _ensure_ee()
    from satellite_embedding.connector import compare_years

    return compare_years(longitude, latitude, year_a, year_b)


def get_area_embedding(
    lon_min: float,
    lat_min: float,
    lon_max: float,
    lat_max: float,
    year: int,
) -> dict:
    """Get the mean satellite embedding vector over a bounding box for a year.

    Use a small bounding box (a few hundred meters) to avoid timeouts.

    Args:
        lon_min: Western longitude bound.
        lat_min: Southern latitude bound.
        lon_max: Eastern longitude bound.
        lat_max: Northern latitude bound.
        year: Calendar year (2017 onward).

    Returns:
        Dict mapping band names (A00–A63) to mean float values.
    """
    _ensure_ee()
    from satellite_embedding.connector import mean_embedding_in_bbox

    return mean_embedding_in_bbox(lon_min, lat_min, lon_max, lat_max, year)


# ---------------------------------------------------------------------------
# Solar client tools
# ---------------------------------------------------------------------------


def get_solar_potential(latitude: float, longitude: float) -> dict:
    """Get rooftop solar potential for the building closest to a location.

    Returns panel capacity, estimated yearly energy, carbon offset, roof area,
    and imagery quality. Data comes from the Google Solar API.

    Args:
        latitude: WGS84 latitude.
        longitude: WGS84 longitude.

    Returns:
        Dict with solar potential summary fields.
    """
    client = _get_solar_client()
    building = client.find_closest_building(latitude, longitude)
    sp = building.solar_potential
    result: dict = {
        "building_name": building.name,
        "imagery_quality": building.imagery_quality,
    }
    if sp:
        result.update(
            {
                "max_panels": sp.max_array_panels_count,
                "panel_capacity_watts": sp.panel_capacity_watts,
                "max_array_area_m2": sp.max_array_area_meters2,
                "max_sunshine_hours_per_year": sp.max_sunshine_hours_per_year,
                "carbon_offset_kg_per_mwh": sp.carbon_offset_factor_kg_per_mwh,
                "panel_lifetime_years": sp.panel_lifetime_years,
                "roof_segments": len(sp.roof_segment_stats),
                "panel_configurations": len(sp.solar_panel_configs),
            }
        )
    return result


def get_solar_financials(latitude: float, longitude: float) -> dict:
    """Get financial analysis for solar installation at a location.

    Returns payback period, estimated savings, and cost details from the
    Google Solar API. Typically uses the largest panel configuration.

    Args:
        latitude: WGS84 latitude.
        longitude: WGS84 longitude.

    Returns:
        Dict with financial analysis fields.
    """
    client = _get_solar_client()
    building = client.find_closest_building(latitude, longitude)
    sp = building.solar_potential
    result: dict = {"building_name": building.name}
    if sp and sp.financial_analyses:
        fa = sp.financial_analyses[-1]
        fd = fa.financial_details
        if fd:
            result["initial_ac_kwh_per_year"] = fd.initial_ac_kwh_per_year
            result["net_metering_allowed"] = fd.net_metering_allowed
            if fd.solar_percentage is not None:
                result["solar_percentage"] = fd.solar_percentage
            if fd.cash_purchase_savings:
                cps = fd.cash_purchase_savings
                if cps.payback_years is not None:
                    result["payback_years"] = cps.payback_years
                if cps.savings:
                    result["lifetime_savings_units"] = cps.savings.units
                    result["lifetime_savings_currency"] = cps.savings.currency_code
            if fd.federal_incentive:
                result["federal_incentive_units"] = fd.federal_incentive.units
    if not result.get("initial_ac_kwh_per_year"):
        result["note"] = "No financial analysis available for this location."
    return result
