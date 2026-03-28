# warsaw-hackathon-2026

Minimal Python connector to the **Google Satellite Embedding** dataset (AlphaEarth Foundations annual embeddings) via **Google Earth Engine**.

- **Dataset (Earth Engine):** [GOOGLE/SATELLITE_EMBEDDING_V1_ANNUAL](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL) — 64 bands (`A00`–`A63`), ~10 m, annual mosaics from 2017 onward.
- **Background:** [AlphaEarth Foundations (DeepMind)](https://deepmind.google/blog/alphaearth-foundations-helps-map-our-planet-in-unprecedented-detail/)

## Quick start (for teammates)

```bash
# 1. Clone & install
git clone <repo-url> && cd warsaw-hackathon-2026
curl -LsSf https://astral.sh/uv/install.sh | sh   # skip if you already have uv
export PATH="$HOME/.local/bin:$PATH"
uv sync

# 2. Authenticate (one-time, opens a browser)
uv run earthengine authenticate

# 3. Set your GCP project id
export EARTH_ENGINE_PROJECT=your-gcp-project-id

# 4. Verify it works
uv run satellite-embedding-demo
```

## Prerequisites

1. A **Google account** with [Earth Engine access](https://earthengine.google.com/signup/) (approval is usually instant).
2. A **Google Cloud project** with the **Earth Engine API** enabled.
   - Go to [console.cloud.google.com](https://console.cloud.google.com) > **APIs & Services** > **Library** > search **"Earth Engine API"** > **Enable**.
3. Your **project id** (not the display name).
   - Find it at [console.cloud.google.com](https://console.cloud.google.com) > click the project dropdown at the top > use the **ID** column.

This MVP uses **interactive OAuth** on your machine (no service account file).

## Setup

Install [uv](https://docs.astral.sh/uv/), then:

```bash
uv sync
```

Set the project id:

```bash
export EARTH_ENGINE_PROJECT=your-gcp-project-id
```

Or copy [`.env.example`](.env.example) to `.env` and load it however you prefer (this repo does not load `.env` automatically to keep dependencies minimal).

### First-time authentication

```bash
uv run earthengine authenticate
```

This opens a browser for Google OAuth. Complete the flow once — credentials are stored locally and you won't need to do it again on the same machine.

## Run the demo

```bash
export EARTH_ENGINE_PROJECT=your-gcp-project-id
uv run satellite-embedding-demo
```

Or:

```bash
uv run python -m satellite_embedding.demo
```

The demo samples the embedding at a fixed point near **Warsaw** for **2023** and prints a short summary.

## Use as a library

```python
from satellite_embedding import init, sample_point, mean_embedding_in_bbox

init()  # or init(project="your-gcp-project-id")
vec = sample_point(21.0122, 52.2297, 2023)

# Optional: mean over a *small* WGS84 bbox (large areas can time out)
means = mean_embedding_in_bbox(21.0, 52.2, 21.02, 52.22, 2023)
```

## Project layout

| Path | Purpose |
|------|--------|
| [`src/satellite_embedding/connector.py`](src/satellite_embedding/connector.py) | `init`, `embedding_image`, `sample_point`, `mean_embedding_in_bbox` |
| [`src/satellite_embedding/demo.py`](src/satellite_embedding/demo.py) | CLI / module entry for the hackathon demo |

## Notes

- Keep **bounding boxes tiny** for `mean_embedding_in_bbox` during live demos to avoid Earth Engine timeouts.
- For headless or CI deployment later, consider a **service account** registered for Earth Engine (not implemented in this MVP).
