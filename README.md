# SpaceTech-2F2E — Earth Trend Detective

NASA Space Apps Challenge team project.

## Project structure

```
detective3d/                 # THE APP: 3D map UI + chat agent (D)
  index.html                 # 3D MapLibre UI (time player, cards, NDVI, heat map, chat panel)
  agent_server.py            # serves the UI + /api/chat agent over the repo's analysis
  data.js, power_data.js,    # generated data the UI reads (committed)
  ndvi_data.js, cities.js
  build_*.py                 # regenerate those data files
  README.md                  # how the app works, LLM setup, data notes (Turkish)
api.py                       # FastAPI functions over the Python modules (C); used by detective3d
power_loader.py              # NASA POWER point/box loader (C)
frontend/                    # earlier React + shadcn/ui UI (C); kept, no longer built or deployed
requirements.txt             # Python dependencies
Dockerfile                   # one container serving detective3d
data/
  raw/                       # 9 raw Giovanni CSVs: <region_id>__<variable_id>.csv (A)
  processed/all_series.csv   # cleaned monthly series used by the app (A)
  SOURCES.md                 # where and when each file was downloaded (A)
  catalog.json               # variables, regions, themes, glossary, hints, context, cases (D)
scripts/
  process_giovanni.py        # data/raw -> data/processed/all_series.csv (A)
  check_data.py              # data quality report (A)
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

With Docker (this is what hosting platforms run):

```bash
docker build -t earth-trend-detective .
docker run -p 8000:8000 earth-trend-detective     # http://localhost:8000
# with the LLM agent:  docker run -p 8000:8000 -e LLM_PROVIDER=groq -e LLM_API_KEY=... earth-trend-detective
```

### Publishing a public link

The `Dockerfile` works on any host that builds Docker images and sets `$PORT`.
Two free options that give a public URL with no login for visitors:

- **Render** (render.com): New → Web Service → connect this GitHub repo →
  Runtime: Docker → Instance type: Free → Create. Add `LLM_PROVIDER` and
  `LLM_API_KEY` under Environment as secrets. The URL looks like
  `https://<name>.onrender.com`. Free instances sleep when idle, so the first
  visit can take ~1 minute.
- **Hugging Face Spaces** (huggingface.co/new-space): SDK: Docker → push this
  repo to the Space, add `app_port: 8000` to the Space's README header and the
  key as a Space secret.

After deploying, open the link in a private/incognito window to check it works
without being signed in.

UI language: the 3D app is in Turkish for now; Space Apps requires English for
the submission.

### Earlier React UI (C)

`frontend/` + `api.py` still run on their own (`uvicorn api:app --reload` and
`cd frontend && npm install && npm run dev`), but they are no longer part of the
Docker image. API endpoints (`api.py`): `/api/meta`, `/api/analysis`,
`/api/overview`, `/api/compare`, `/api/suggest`, `/api/point`, `/api/box`.

## Contribution workflow

**Do not push directly to `main`.** Every change goes through a pull request.

1. Update your local `main`: `git checkout main && git pull`
2. Create a branch: `git checkout -b feature/<role>-<short-topic>` (e.g. `feature/d-catalog-detective`)
3. Commit your work and push the branch: `git push -u origin <branch>`
4. Open a pull request into `main` and ask a teammate to review.
5. Merge with **Squash and merge**, then delete the branch.
6. If you add a dependency, add it to `requirements.txt` in the same PR.
