"""Runnable demo: sample Satellite Embedding at a fixed point (Warsaw)."""

from __future__ import annotations

from satellite_embedding.connector import init, sample_point


def main() -> None:
    init()
    # Approximate center of Warsaw (lon, lat).
    lon, lat = 21.0122, 52.2297
    year = 2023
    props = sample_point(lon, lat, year)
    keys = sorted(props.keys())
    preview = {k: round(props[k], 6) for k in keys[:5]}
    print(f"Satellite Embedding sample at ({lat:.4f}, {lon:.4f}), year {year}")
    print(f"First 5 bands (of {len(keys)}): {preview}")


if __name__ == "__main__":
    main()
