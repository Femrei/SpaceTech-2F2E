# SpaceTech-2F2E

NASA Space Apps Challenge team project.

## Project structure

```
api.py             # FastAPI backend: JSON API over the Python modules (owner: C)
frontend/          # React + Vite + TypeScript + Tailwind + shadcn/ui UI (owner: C)
requirements.txt   # Python dependencies
data/              # small curated data files (e.g. catalog.json)
src/               # Python modules: data_loader (A), trend (B), mock_data (B), detective (D)
src/stubs/         # TEMP placeholder for D's detective module until it lands
scripts/           # A's Giovanni processing and data checks
tests/             # tests and validation scripts
```

The React UI talks to `api.py`, which imports `src.data_loader`, `src.trend`
and `src.detective` unchanged. Until a module lands on `main`, `api.py` falls
back to its placeholder in `src/stubs/` (the UI shows a warning when it does).

## Getting started

Needs Python 3.10–3.13 (the pinned numpy/scipy/pandas have no 3.14 wheels) and Node.js 20+.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m src.mock_data      # writes data/processed/all_series.csv (B's synthetic data) until A's real data is in
cd frontend && npm install && cd ..
```

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
| Detective Mode | Theme → suggestions → investigation, with clue + "follow the clue" | D `THEMES`, `suggest`, `next_step_hint` |
| Case Files | Ready-made cases; two-region cases open the compare view | D `get_cases` |
| Compare | Same measurement, two regions, same/opposite direction summary | B `compare_trends` |

API endpoints (`api.py`): `/api/meta`, `/api/analysis`, `/api/overview`,
`/api/compare`, `/api/suggest`.

## Contribution workflow

**Do not push directly to `main`.** Every change goes through a pull request.

1. Update your local `main`: `git checkout main && git pull`
2. Create a branch: `git checkout -b feature/<role>-<short-topic>` (e.g. `feature/d-catalog-detective`)
3. Commit your work and push the branch: `git push -u origin <branch>`
4. Open a pull request into `main` and ask a teammate to review.
5. If you add a dependency, add it to `requirements.txt` in the same PR.
