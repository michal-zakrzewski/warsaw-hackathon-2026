"""Minimal Earth Engine connector for AlphaEarth Satellite Embedding (annual mosaic)."""

from __future__ import annotations

import os

import ee

COLLECTION_ID = "GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL"
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
    region = point.buffer(15)
    fc = img.sample(region=region, scale=10, numPixels=1, geometries=False)
    feature = fc.first().getInfo()
    if feature is None:
        return {}
    props = feature.get("properties") or {}
    return {k: float(v) for k, v in props.items() if k in BANDS}


def compare_years(
    lon: float,
    lat: float,
    year_a: int,
    year_b: int,
) -> dict:
    """Dot-product similarity between embeddings at the same point in two years.

    Returns a value between -1 and 1 (unit-length vectors). A score near 1.0
    means the land-use context is stable; lower values indicate change.
    """
    vec_a = sample_point(lon, lat, year_a)
    vec_b = sample_point(lon, lat, year_b)
    if not vec_a or not vec_b:
        return {
            "similarity": None,
            "year_a": year_a,
            "year_b": year_b,
            "error": "No satellite embedding data found for the given coordinates/year.",
        }
    shared = sorted(set(vec_a) & set(vec_b))
    dot = sum(vec_a[k] * vec_b[k] for k in shared)
    return {"similarity": dot, "year_a": year_a, "year_b": year_b}


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
