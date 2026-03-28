"""Minimal Earth Engine connector for AlphaEarth Satellite Embedding (annual mosaic)."""

from __future__ import annotations

import os

import ee

COLLECTION_ID = "GOOGLE/SATELLITE_EMBEDDING_V1_ANNUAL"
BANDS = [f"A{i:02d}" for i in range(64)]

_MISSING_PROJECT = (
    "Set environment variable EARTH_ENGINE_PROJECT to your Google Cloud project id "
    "(with Earth Engine API enabled), or pass project= to init()."
)


def init(project: str | None = None) -> None:
    """Initialize Earth Engine. Call once per process after ``ee.Authenticate()``."""
    resolved = project or os.environ.get("EARTH_ENGINE_PROJECT")
    if not resolved or not resolved.strip():
        raise ValueError(_MISSING_PROJECT)
    ee.Initialize(project=resolved.strip())


def embedding_image(year: int) -> ee.Image:
    """Return the annual embedding mosaic for ``year`` (64 bands A00–A63)."""
    col = ee.ImageCollection(COLLECTION_ID).filter(
        ee.Filter.calendarRange(year, year, "year")
    )
    return col.mosaic().select(BANDS)


def sample_point(lon: float, lat: float, year: int) -> dict[str, float]:
    """Sample the embedding at a WGS84 point (~10 m scale). Returns band -> value."""
    img = embedding_image(year)
    point = ee.Geometry.Point([lon, lat])
    # Small buffer so sampling has a non-degenerate region at the target scale.
    region = point.buffer(15)
    fc = img.sample(region=region, scale=10, numPixels=1, geometries=False)
    props = fc.first().getInfo().get("properties") or {}
    return {k: float(v) for k, v in props.items() if k in BANDS}


def mean_embedding_in_bbox(
    lon_min: float,
    lat_min: float,
    lon_max: float,
    lat_max: float,
    year: int,
) -> dict[str, float]:
    """Mean of each embedding band over a WGS84 bounding box. Use a *small* AOI for demos."""
    img = embedding_image(year)
    region = ee.Geometry.Rectangle([lon_min, lat_min, lon_max, lat_max])
    stats = img.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=10,
        maxPixels=1_000_000_000,
    )
    raw = stats.getInfo() or {}
    return {k: float(v) for k, v in raw.items() if k in BANDS}
