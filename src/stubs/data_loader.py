# TEMP STUB — will be replaced by A (src/data_loader.py)
"""Stand-in for A's data loader.

Reads ``data/processed/all_series.csv`` if it exists (e.g. produced by B's
``python -m src.mock_data``); otherwise generates realistic mock series in
memory so the app can run with no data files at all.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DOWNLOADED_ON = "N/A (mock data)"

_CSV = Path(__file__).resolve().parent.parent.parent / "data/processed/all_series.csv"

# (mean, seasonal amplitude, peak month, trend per decade, noise sd)
_MOCK_PARAMS = {
    ("konya", "temp"): (12.0, 11.5, 7, 0.6, 1.2),
    ("van", "temp"): (9.0, 13.0, 8, 0.5, 1.3),
    ("black_sea", "temp"): (12.5, 8.5, 8, 0.4, 1.0),
    ("konya", "precip"): (30.0, 18.0, 12, -2.5, 12.0),
    ("van", "precip"): (40.0, 22.0, 4, -0.5, 15.0),
    ("black_sea", "precip"): (110.0, 45.0, 10, 6.0, 30.0),
    ("konya", "soil_moisture"): (22.0, 6.0, 2, -1.2, 1.5),
    ("van", "soil_moisture"): (26.0, 7.0, 4, -0.3, 1.8),
    ("black_sea", "soil_moisture"): (32.0, 4.0, 1, 0.2, 1.5),
}


def _generate_mock() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    dates = pd.date_range("2001-01-01", "2025-12-01", freq="MS")
    months = dates.month.to_numpy()
    years = (dates.year.to_numpy() - 2001) + (months - 1) / 12
    frames = []
    for (region_id, variable_id), (mean, amp, peak, trend, sd) in _MOCK_PARAMS.items():
        season = amp * np.cos(2 * np.pi * (months - peak) / 12)
        values = mean + season + trend / 10 * years + rng.normal(0, sd, len(dates))
        if variable_id != "temp":
            values = np.clip(values, 0, None)
        values[rng.random(len(dates)) < 0.01] = np.nan
        frames.append(pd.DataFrame({
            "date": dates, "region_id": region_id,
            "variable_id": variable_id, "value": values,
        }))
    return pd.concat(frames, ignore_index=True)


@lru_cache(maxsize=1)
def load_all() -> pd.DataFrame:
    if _CSV.exists():
        return pd.read_csv(_CSV, parse_dates=["date"])
    return _generate_mock()


def load_series(region_id: str, variable_id: str) -> pd.Series:
    df = load_all()
    sub = df[(df.region_id == region_id) & (df.variable_id == variable_id)]
    if sub.empty:
        raise KeyError(f"No data for region={region_id!r}, variable={variable_id!r}")
    s = sub.set_index("date")["value"].sort_index().asfreq("MS")
    s.name = variable_id
    return s


def available_pairs() -> list[tuple[str, str]]:
    df = load_all()
    return sorted(set(zip(df.region_id, df.variable_id)))
