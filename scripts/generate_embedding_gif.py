"""Generate a temporal GIF of AlphaEarth Satellite Embeddings for a location.

Renders 3 embedding bands as RGB channels across multiple years,
producing an animated GIF that visualises land-use stability over time.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

import ee
import numpy as np
from PIL import Image, ImageDraw, ImageFont

COLLECTION_ID = "GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL"
YEARS = list(range(2017, 2024))
RGB_BANDS = ["A05", "A15", "A30"]
BUFFER_M = 1500
SCALE = 10
IMG_SIZE = 512


def init_ee() -> None:
    import os
    from dotenv import load_dotenv

    env_path = Path(__file__).resolve().parent.parent / "green_agent" / ".env"
    load_dotenv(env_path)
    project = os.environ.get("EARTH_ENGINE_PROJECT", "")
    if not project:
        sys.exit("Set EARTH_ENGINE_PROJECT in green_agent/.env")
    ee.Initialize(project=project.strip())


def fetch_rgb_tile(lon: float, lat: float, year: int) -> np.ndarray:
    """Fetch a small RGB tile from the embedding dataset for one year."""
    col = ee.ImageCollection(COLLECTION_ID).filter(
        ee.Filter.calendarRange(year, year, "year")
    )
    img = col.mosaic().select(RGB_BANDS)

    point = ee.Geometry.Point([lon, lat])
    region = point.buffer(BUFFER_M).bounds()

    url = img.getThumbURL({
        "region": region.getInfo()["coordinates"],
        "dimensions": IMG_SIZE,
        "format": "png",
        "min": -0.3,
        "max": 0.3,
    })

    import urllib.request
    with urllib.request.urlopen(url) as resp:
        data = resp.read()

    pil_img = Image.open(io.BytesIO(data)).convert("RGB")
    return np.array(pil_img)


def add_label(img_array: np.ndarray, text: str) -> Image.Image:
    """Overlay a year label on the image."""
    pil = Image.fromarray(img_array)
    draw = ImageDraw.Draw(pil)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
    except OSError:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x, y = IMG_SIZE - tw - 20, IMG_SIZE - th - 20

    draw.rectangle([x - 8, y - 4, x + tw + 8, y + th + 4], fill=(0, 0, 0, 180))
    draw.text((x, y), text, fill=(255, 255, 255), font=font)
    return pil


def main() -> None:
    if len(sys.argv) < 3:
        sys.exit(f"Usage: {sys.argv[0]} <lat> <lon> [output.gif]")

    lat, lon = float(sys.argv[1]), float(sys.argv[2])
    out_path = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("demo/embedding_timelapse.gif")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Coordinates: {lat}, {lon}")
    print(f"Bands: {RGB_BANDS} → RGB")
    print(f"Years: {YEARS[0]}–{YEARS[-1]}")
    print(f"Buffer: {BUFFER_M}m, Scale: {SCALE}m, Size: {IMG_SIZE}px")
    print()

    init_ee()

    frames: list[Image.Image] = []
    for year in YEARS:
        print(f"  Fetching {year}...", end=" ", flush=True)
        arr = fetch_rgb_tile(lon, lat, year)
        frame = add_label(arr, str(year))
        frames.append(frame)
        print("done")

    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        duration=1200,
        loop=0,
        optimize=True,
    )
    print(f"\nSaved {out_path}  ({out_path.stat().st_size / 1024:.0f} KB)")
    print(f"  {len(frames)} frames, 1.2s per frame")


if __name__ == "__main__":
    main()
