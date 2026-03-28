ADK-based green-finance site assessment agent that combines **AlphaEarth Satellite Embeddings** (land-use context, stability, change detection) with the **Google Solar API** (rooftop solar potential, financial analysis) to evaluate locations for green investments.

## What it does

Ask natural-language questions like:

- "Is the area at 21.01, 52.23 suitable for a farm investment?"
- "How stable has this location been over the last 5 years?"
- "What is the solar potential for the building at 37.44, -122.14?"
- "Give me a full site assessment for coordinates 50.06, 19.94"

The agent autonomously decides which tools to call and synthesizes the results into a concise assessment.

## Project structure

```
green_agent/
├── agent.py           — root_agent definition + system prompt
├── tools.py           — tool wrappers for satellite_embedding + solar_client
├── __init__.py        — re-exports root_agent
├── .env               — API keys (git-ignored)
└── green_agent_docs.md
```

## Tools available to the agent

| Tool | Source | Description |
|------|--------|-------------|
| `get_site_embedding` | AlphaEarth / Earth Engine | 64-d embedding vector at a point for a year |
| `compare_site_years` | AlphaEarth / Earth Engine | Similarity score between two years (stability) |
| `get_area_embedding` | AlphaEarth / Earth Engine | Mean embedding over a small bounding box |
| `get_solar_potential` | Google Solar API | Rooftop panel capacity, energy, carbon offset |
| `get_solar_financials` | Google Solar API | Payback period, savings, incentives |

## Setup

### 1. Install dependencies

From the repo root:

```bash
uv sync
```

### 2. Authenticate Earth Engine (one-time)

```bash
uv run earthengine authenticate
```

### 3. Configure API keys

Fill in `green_agent/.env`:

```
GOOGLE_API_KEY=your-gemini-api-key
EARTH_ENGINE_PROJECT=your-gcp-project-id
GOOGLE_SOLAR_API_KEY=your-solar-api-key
```

- **GOOGLE_API_KEY**: Gemini API key from [aistudio.google.com/apikey](https://aistudio.google.com/apikey) (free tier works).
- **EARTH_ENGINE_PROJECT**: GCP project id with Earth Engine API enabled.
- **GOOGLE_SOLAR_API_KEY**: Google Maps Platform key with Solar API enabled.

### 4. Run

**Web UI** (recommended for demos):

```bash
uv run adk web
```

Then open [http://localhost:8000](http://localhost:8000) and select **green_finance_agent** from the dropdown.

**CLI**:

```bash
uv run adk run green_agent
```

## Example prompts to try

1. "Assess the site at longitude 21.01, latitude 52.23 for agricultural investment"
2. "Compare land-use stability at 21.01, 52.23 between 2019 and 2023"
3. "What's the solar potential at 37.4450, -122.1390?"
4. "Full green-finance assessment for 50.06, 19.94 (Krakow)"

## Limitations

- **Solar API coverage**: mainly US, Japan, Germany, Australia, India, and select European cities. Returns an error for uncovered locations.
- **Satellite embeddings**: available from 2017 onward. Keep bounding boxes small to avoid Earth Engine timeouts.
- **Agent model**: uses `gemini-2.0-flash` (fast, free-tier friendly). Can be changed in `agent.py`.
