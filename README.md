# SpaceTech-2F2E

NASA Space Apps Challenge team project.

## Project structure

```
app.py             # Streamlit app entry point (owner: C)
requirements.txt   # Python dependencies
data/              # small curated data files (e.g. catalog.json)
src/               # application modules (e.g. detective.py, charts.py)
src/stubs/         # TEMP placeholders for modules not merged yet (delete when all land)
tests/             # tests and validation scripts
```

## Getting started

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Contribution workflow

**Do not push directly to `main`.** Every change goes through a pull request.

1. Update your local `main`: `git checkout main && git pull`
2. Create a branch: `git checkout -b feature/<role>-<short-topic>` (e.g. `feature/d-catalog-detective`)
3. Commit your work and push the branch: `git push -u origin <branch>`
4. Open a pull request into `main` and ask a teammate to review.
5. If you add a dependency, add it to `requirements.txt` in the same PR.
