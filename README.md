# SpaceTech-2F2E — Earth Trend Detective

NASA Space Apps Challenge team project.

## Project structure

```
app.py                       # Streamlit app entry point (C)
requirements.txt             # Python dependencies
data/
  raw/                       # 9 raw Giovanni CSVs: <region_id>__<variable_id>.csv (A)
  processed/all_series.csv   # cleaned monthly series used by the app (A; mock version from B)
  catalog.json               # variables, regions, glossary, cases (D)
scripts/
  process_giovanni.py        # data/raw -> data/processed/all_series.csv (A)
  check_data.py              # data quality report (A)
src/
  data_loader.py             # load_series, available_pairs (A)
  mock_data.py               # synthetic all_series.csv until real data is in (B)
  trend.py                   # analyze_trend, interpret, compare_trends (B)
  charts.py                  # Plotly charts (C)
  detective.py               # catalog access, suggestions, hints (D)
tests/                       # pytest tests
```

## Getting started

Python 3.10–3.13 (the pinned numpy/scipy/pandas versions have no wheels for 3.14 yet).

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m src.mock_data      # only needed until the real data/processed/all_series.csv is committed
streamlit run app.py
python -m pytest
```

## Contribution workflow

**Do not push directly to `main`.** Every change goes through a pull request.

1. Update your local `main`: `git checkout main && git pull`
2. Create a branch: `git checkout -b feature/<role>-<short-topic>` (e.g. `feature/d-catalog-detective`)
3. Commit your work and push the branch: `git push -u origin <branch>`
4. Open a pull request into `main` and ask a teammate to review.
5. Merge with **Squash and merge**, then delete the branch.
6. If you add a dependency, add it to `requirements.txt` in the same PR.
