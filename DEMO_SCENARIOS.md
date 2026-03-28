# Demo Scenarios

Two pre-tested scenarios that showcase different capabilities of the Concierge green-finance agent.

## Prerequisites

```bash
# 1. Fill in green_agent/.env with your API keys
GOOGLE_API_KEY=<your-gemini-key>
EARTH_ENGINE_PROJECT=<your-gcp-project>
GOOGLE_SOLAR_API_KEY=<your-solar-key>

# 2. Clear stale sessions
rm -f green_agent/.adk/session.db

# 3. Start ADK backend (from repo root)
uv run adk api_server . --port 8000

# 4. Start frontend (separate terminal)
cd frontend && npm run dev
```

Open http://localhost:5173/ and click **Start**.

---

## Scenario 1: US Farm — Solar + Satellite Stability

**What it demonstrates:** Full-stack analysis combining Google Solar API (real rooftop data) with AlphaEarth satellite embeddings (land-use stability). No building photo, no building details — Step 2 is skipped entirely. The agent tailors advice to agriculture, including organic certification eligibility.

### Form inputs

**Step 1 — Business Info:**

| Field | Value |
|---|---|
| Business Name | `Green Valley Farm` |
| Business Type | `Farm / Agriculture` |
| Address | `Rural Road, Mountain View, CA` |
| Latitude | `37.3861` |
| Longitude | `-122.0839` |
| Annual Energy | `85000` |
| Budget | ~$30k |
| Sustainability Goal | `Install solar panels on barn roof and assess land stability for organic certification` |

**Step 2 — Building Details:** Skip (no photo, leave footprint area empty).

### What to expect

- **Satellite embedding:** Stability score ~0.956 (2017–2023) — very stable land-use context
- **Solar API:** 156 panels, 306 m² roof, ~12,098 kWh/yr output, $7,807 federal incentive
- **Agent insight:** Notes that solar covers only ~14% of demand, install cost ($187k) exceeds budget, recommends phased approach and USDA REAP grants
- **Organic certification:** Agent connects the high stability score to eligibility for organic certification
- **Dynamic stat cards:** Solar potential, CO₂ reduction, and site stability will populate. Heat Loss card will show "—" (no building analysis requested).

### Key talking points

- Real satellite data from Google DeepMind's AlphaEarth Foundations
- Real rooftop solar analysis from Google Solar API
- Agent doesn't blindly recommend — flags budget mismatch and suggests alternatives
- Context-aware: references USDA agricultural programs, not generic advice
- Sets the baseline: "the system is useful with just an address and coordinates"

---

## Scenario 2: Warsaw Office/Industrial — Photo-Driven Heat Loss + Solar + Satellite

**What it demonstrates:** Different geography (EU), different business type (manufacturing), and the **killer feature** — a building photo is uploaded, and Gemini visually analyzes it to identify wall materials, windows, roof type, cracks, degradation, and insulation signs. The visual observations feed directly into a physics-based heat-loss calculation (EN ISO 6946 / EN 12831). All three tool categories fire in one analysis.

### Form inputs

**Step 1 — Business Info:**

| Field | Value |
|---|---|
| Business Name | `EcoSteel Annopol` |
| Business Type | `Manufacturing` |
| Address | `ul. Annopol 4, Warsaw, Poland` |
| Latitude | `52.3012` |
| Longitude | `21.0220` |
| Annual Energy | `200000` |
| Budget | ~$80k |
| Sustainability Goal | `Reduce heating costs and carbon footprint through energy efficiency upgrades` |

**Step 2 — Building Details:**

| Field | Value |
|---|---|
| Building Photo | Upload `demo/demo_factory.png` |
| Ground Floor Area | `1200` m² |

Everything else (building type, roof type, wall material, window type, floors, floor height) is identified by Gemini from the photo.

### What to expect

- **Vision analysis:** Gemini examines the photo and identifies:
  - Glass curtain wall facade with red accent panels → `glass_curtain` wall finish
  - Steel frame structure
  - Flat roof (covering not visible) → `bitumen_membrane` assumed
  - Double-glazed windows (modern aluminum frames)
  - 3 visible floors, estimated WWR ~0.65
  - No visible cracks, no degradation, no external insulation
  - Vision confidence ~0.8
- **Heat-loss estimation:** Base heat loss **~179 kW** (range: 52–529 kW)
  - Infiltration: ~75 kW (dominant)
  - Windows: ~53 kW (high due to glass curtain wall)
  - Walls: ~25 kW
  - Roof: ~12 kW
  - Geometry confidence: ~77% (footprint provided, floors estimated from photo, floor height defaulted)
- **Satellite embedding:** Stability score ~0.95 (2017–2023) — very stable
- **Solar API:** 111 panels, 218 m², ~44.4 MWh/yr, ~33.5 tons CO₂/yr offset
- **Dynamic stat cards:** All four populated with real data from the agent's JSON output
- **Building Energy Profile:** Shows dominant loss source, geometry confidence, payback (if calculable)
- **Dynamic "Why this is the best option" insights:** 3 agent-generated reasons specific to the analysis (e.g. solar generation potential, carbon offset, energy savings)

### Key talking points

- **Photo-to-analysis pipeline:** Upload a photo + enter floor area → AI identifies materials → physics-based heat-loss estimate. That's the "wow" moment.
- Agent used **three different tool categories** (satellite, solar, heat-loss) in one analysis
- Gemini correctly identified **glass curtain wall** as the dominant heat-loss surface from the photo
- User only provided **one number** (floor area) — everything else came from the photo
- Results page stat cards, building energy profile, and "why this is the best option" insights are all **dynamically generated** from the agent's structured JSON output
- Recommended EU-relevant financing (green loans, sustainability-linked financing) — not US programs
- Same system, completely different advice for different contexts

---

## Side-by-side comparison

| | Mountain View Farm | Warsaw Office/Industrial |
|---|---|---|
| Photo uploaded | No | Yes (`demo/demo_factory.png`) |
| Tools used | Satellite + Solar | Satellite + Solar + Heat-loss + Vision |
| Dynamic stat cards | Solar + CO₂ + Stability | All 4 (Heat Loss + Solar + CO₂ + Stability) |
| Primary recommendation | Phased solar + organic cert | Solar PV or envelope upgrades (varies by run) |
| Fastest payback | N/A (over budget) | ~6–8 years (depends on recommendation) |
| Annual savings | — | Varies — agent estimates based on analysis |
| CO₂ reduction | ~5 tons/yr | ~33.5 tons/yr (solar) + envelope savings |
| Financing referenced | USDA REAP grants | Green loans, sustainability-linked financing |
| Region-specific | California net metering | Polish energy rates |

---

## Presentation story arc

1. **Scenario 1** — "Here's a farm in California. We fill in an address and coordinates. The system pulls real satellite data and real solar rooftop data. It gives smart, region-specific advice." *(Baseline — shows the system is useful)*
2. **Scenario 2** — "Now let's go harder. A factory in Warsaw. This time we upload a photo of the building and enter the floor area — that's it. Watch what happens — the AI examines the facade, identifies glass curtain walls, counts floors, and runs a physics-based heat-loss calculation. It combines that with satellite stability data and solar potential for a complete green-finance assessment from a single photo and one number." *(Wow moment — multimodal AI + physics engine)*
