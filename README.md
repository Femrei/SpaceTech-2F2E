# SpaceTech-2F2E — Earth Trend Detective

NASA Space Apps Challenge team project.

## Project structure

```
api.py                       # FastAPI backend: JSON API over the Python modules (C)
frontend/                    # React + Vite + TypeScript + Tailwind + shadcn/ui UI (C)
  DESIGN.md                  # visual direction, tokens, fonts (C)
requirements.txt             # Python dependencies
Dockerfile                   # one container: built UI + API (C)
data/
  raw/                       # 9 raw Giovanni CSVs: <region_id>__<variable_id>.csv (A)
  processed/all_series.csv   # cleaned monthly series used by the app (A)
  SOURCES.md                 # where and when each file was downloaded (A)
  catalog.json               # variables, regions, themes, glossary, hints, cases (D)
scripts/
  process_giovanni.py        # data/raw -> data/processed/all_series.csv (A)
  check_data.py              # data quality report (A)
src/
  data_loader.py             # load_series, available_pairs (A)
  mock_data.py               # synthetic all_series.csv for testing without real data (B)
  trend.py                   # analyze_trend, interpret, compare_trends (B)
  detective.py               # catalog access, suggestions, next-step hints (D)
tests/                       # pytest tests (B, D)
```

The React UI talks to `api.py`, which imports `src.data_loader`, `src.trend`
and `src.detective` unchanged. If `data/raw/` has no Giovanni CSVs (i.e. the
data came from `src.mock_data`), the UI shows a "synthetic data" warning.

## Getting started

Needs Python 3.10–3.13 (the pinned numpy/scipy/pandas have no 3.14 wheels) and Node.js 20+.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cd frontend && npm install && cd ..
python -m pytest             # B's and D's tests
```

The real data (`data/processed/all_series.csv`) is committed. To rebuild it from
the raw Giovanni files run `python scripts/process_giovanni.py`.

Development (two terminals):

```bash
uvicorn api:app --reload          # backend on http://localhost:8000
cd frontend && npm run dev        # UI on http://localhost:5173 (proxies /api to :8000)
```

Production / deploy (one server serves both the API and the built UI):

```bash
cd frontend && npm run build && cd ..
uvicorn api:app --host 0.0.0.0 --port 8000
```

With Docker (same thing in one container, this is what hosting platforms run):

```bash
docker build -t earth-trend-detective .
docker run -p 8000:8000 earth-trend-detective     # http://localhost:8000
```

### Publishing a public link

The `Dockerfile` works on any host that builds Docker images and sets `$PORT`.
Two free options that give a public URL with no login for visitors:

- **Render** (render.com): New → Web Service → connect this GitHub repo →
  Runtime: Docker → Instance type: Free → Create. The URL looks like
  `https://<name>.onrender.com`. Free instances sleep when idle, so the first
  visit can take ~1 minute.
- **Hugging Face Spaces** (huggingface.co/new-space): SDK: Docker → push this
  repo to the Space, and add `app_port: 8000` to the Space's README header.

After deploying, open the link in a private/incognito window to check it works
without being signed in.

UI language: set `LANG` in `frontend/src/lib/i18n.ts` (`"tr"` during development,
`"en"` for the final submission).

### App tabs

| Tab | What it does | Uses |
|---|---|---|
| Dashboard | Region + measurement picker with map, KPI tiles, Simple/Detailed chart, plain-language explanation, all-regions grid | A `load_series`, B `analyze_trend`, `interpret` |
| Detective Mode | Theme → suggestions → investigation, with clue + "follow the clue" | D `THEMES`, `suggest`, `next_step` |
| Compare | Same measurement, two regions, same/opposite direction summary | B `compare_trends` |

API endpoints (`api.py`): `/api/meta`, `/api/analysis`, `/api/overview`,
`/api/compare`, `/api/suggest`.

## Contribution workflow

**Do not push directly to `main`.** Every change goes through a pull request.

1. Update your local `main`: `git checkout main && git pull`
2. Create a branch: `git checkout -b feature/<role>-<short-topic>` (e.g. `feature/d-catalog-detective`)
3. Commit your work and push the branch: `git push -u origin <branch>`
4. Open a pull request into `main` and ask a teammate to review.
5. Merge with **Squash and merge**, then delete the branch.
6. If you add a dependency, add it to `requirements.txt` in the same PR.
