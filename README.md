# SpaceTech-2F2E — Earth Trend Detective

NASA Space Apps Challenge team project.

## Project structure

```
detective3d/                 # THE APP: 3D map UI + chat agent (D)
  index.html                 # 3D MapLibre UI in Turkish and English (decision card, enlargeable chart,
                             # auto tour, time player, NDVI imagery layer, yearly stripes, chat panel)
  agent_server.py            # serves the UI + /api/chat agent over the repo's analysis
  data.js, power_data.js,    # generated data the UI reads (committed)
  cities.js
  build_*.py                 # regenerate those data files
  README.md                  # how the app works, LLM setup, data notes (Turkish)
api.py                       # FastAPI functions over the Python modules (C); used by detective3d
power_loader.py              # NASA POWER point/box loader (C)
legacy/frontend/             # earlier React + shadcn/ui UI (C); kept for reference, not built or deployed
requirements.txt             # Python dependencies
data/
  raw/                       # 9 raw Giovanni CSVs: <region_id>__<variable_id>.csv (A)
  processed/all_series.csv   # cleaned monthly series used by the app (A)
  SOURCES.md                 # where and when each file was downloaded (A)
  catalog.json               # variables, regions, themes, glossary, hints, context (D)
scripts/
  process_giovanni.py        # data/raw -> data/processed/all_series.csv (A)
  check_data.py              # data quality report (A)
  check_bbox_water.py        # share of each region box that is sea or lake (see data/SOURCES.md)
src/
  data_loader.py             # load_series, available_pairs (A)
  mock_data.py               # synthetic all_series.csv for testing without real data (B)
  trend.py                   # analyze_trend, interpret, compare_trends (B)
  detective.py               # catalog access, suggestions, next-step hints, context (D)
tests/                       # pytest tests (B, D)
```

`detective3d/agent_server.py` imports `api`, `src.trend` and `src.detective`
unchanged: every number in the UI and in the chat comes from B's analysis and
D's catalog, never from the LLM.

## Getting started

Needs Python 3.10–3.13 (the pinned numpy/scipy/pandas have no 3.14 wheels).

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m pytest                       # B's and D's tests
python detective3d/agent_server.py     # app on http://localhost:8765
```

The browser needs internet access (map tiles and the MapLibre library come from CDNs).

The chat agent works without any key in offline (rule-based) mode. For the full
LLM agent copy `detective3d/.env.example` to `detective3d/.env` and add a free
key (Groq recommended); see `detective3d/README.md`. `.env` is git-ignored:
never commit a key.

The real data (`data/processed/all_series.csv`) is committed. To rebuild it from
the raw Giovanni files run `python scripts/process_giovanni.py`; to regenerate the
app's data files run `python detective3d/build_data.py`.

To show the app on another computer, run the same two commands there (Python and
internet access are all it needs). To open it from other devices on the same network,
start it with `HOST=0.0.0.0`.

UI language: the 3D app has a TR / EN switch (top right). It opens in English unless
the browser language is Turkish, and remembers the choice. Space Apps requires
English for the submission, so demo and record it in EN mode.

### What the app answers

Variable → region → time series → statistics, in that order:

1. Pick a variable (precipitation, soil moisture, air temperature) and a region, or any
   place in Türkiye with **Pick an area** (click the map or search a place name).
2. The **decision card** at the top of the left panel says what is changing, where, how
   fast (Sen slope per decade and %), whether it is statistically significant (seasonal
   Mann-Kendall p-value) and, if it is not, roughly how many more years of data it would
   take, or that the trend is too weak to tell.
3. **Enlarge chart** opens the series with axes, a hover readout, a raw / deseasonalised
   switch, the Sen trend line and its 95% confidence band.
4. The hint box explains the variable and what the trend means; **Next clue** follows the
   catalog's detective hint to the next variable or region.

### Earlier React UI (C)

`legacy/frontend/` + `api.py` still run on their own (`uvicorn api:app --reload` and
`cd legacy/frontend && npm install && npm run dev`), but the team uses the 3D app above.
API endpoints (`api.py`): `/api/meta`, `/api/analysis`,
`/api/overview`, `/api/compare`, `/api/suggest`, `/api/point`, `/api/box`.

## Contribution workflow

**Do not push directly to `main`.** Every change goes through a pull request.

1. Update your local `main`: `git checkout main && git pull`
2. Create a branch: `git checkout -b feature/<role>-<short-topic>` (e.g. `feature/d-catalog-detective`)
3. Commit your work and push the branch: `git push -u origin <branch>`
4. Open a pull request into `main` and ask a teammate to review.
5. Merge with **Squash and merge**, then delete the branch.
6. If you add a dependency, add it to `requirements.txt` in the same PR.
