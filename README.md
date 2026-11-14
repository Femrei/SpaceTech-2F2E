# SpaceTech-2F2E

NASA Space Apps Challenge team project.

## Project structure

```
api.py             # FastAPI backend: JSON API over the Python modules (owner: C)
frontend/          # React + Vite + TypeScript + Tailwind + shadcn/ui UI (owner: C)
requirements.txt   # Python dependencies
data/              # small curated data files (e.g. catalog.json)
src/               # Python modules: data_loader (A), trend (B), detective (D)
src/stubs/         # TEMP placeholders for modules not merged yet (delete when all land)
tests/             # tests and validation scripts
```

The React UI talks to `api.py`, which imports `src.data_loader`, `src.trend`
and `src.detective` unchanged. Until a module lands on `main`, `api.py` falls
back to its placeholder in `src/stubs/` (the UI shows a warning when it does).

## Getting started

Needs Python 3.12+ and Node.js 20+.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
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

UI language: set `LANG` in `frontend/src/lib/i18n.ts` (`"tr"` during development,
`"en"` for the final submission).

## Contribution workflow

**Do not push directly to `main`.** Every change goes through a pull request.

1. Update your local `main`: `git checkout main && git pull`
2. Create a branch: `git checkout -b feature/<role>-<short-topic>` (e.g. `feature/d-catalog-detective`)
3. Commit your work and push the branch: `git push -u origin <branch>`
4. Open a pull request into `main` and ask a teammate to review.
5. If you add a dependency, add it to `requirements.txt` in the same PR.
