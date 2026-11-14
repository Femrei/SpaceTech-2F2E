"""Synthetic monthly time series so the rest of the team can work before real data arrives.

Run:
    python -m src.mock_data

Writes ``data/processed/all_series.csv`` in long format, one row per
(region, variable, month):

    date,region,variable,value,unit
    2001-01-01,konya,precip,41.27,mm/month
    ...

Each series = long-term mean + seasonal cycle + linear trend + Gaussian noise.
About 1% of the values are replaced by NaN at random so every consumer
is exercised with missing data. The random seed is fixed, so the output is
reproducible.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

DEFAULT_PATH = Path("data/processed/all_series.csv")

START = "2001-01-01"
END = "2025-12-01"
NAN_FRACTION = 0.01
SEED = 42

# (region, variable): mean, seasonal amplitude, phase month of the peak,
# trend per decade, noise std, unit, lower physical bound
RECIPES: dict[tuple[str, str], dict] = {
    ("konya", "precip"): dict(mean=27.0, amp=18.0, peak=1, trend=-1.5, noise=9.0, unit="mm/month", floor=0.0),
    ("konya", "soil_moisture"): dict(mean=25.0, amp=6.0, peak=3, trend=-1.2, noise=1.5, unit="kg/m2", floor=0.0),
    ("konya", "temperature"): dict(mean=11.5, amp=11.0, peak=7, trend=0.5, noise=1.0, unit="degC", floor=None),
    ("konya", "ndvi"): dict(mean=0.22, amp=0.08, peak=5, trend=0.0, noise=0.02, unit="1", floor=0.0),
}


def _make_series(index: pd.DatetimeIndex, recipe: dict, rng: np.random.Generator) -> np.ndarray:
    month = np.asarray(index.month)
    years = np.asarray(index.year - index.year[0]) + (month - 1) / 12.0
    seasonal = recipe["amp"] * np.cos(2 * np.pi * (month - recipe["peak"]) / 12.0)
    trend = recipe["trend"] / 10.0 * years
    noise = rng.normal(0.0, recipe["noise"], size=len(index))
    values = recipe["mean"] + seasonal + trend + noise
    if recipe["floor"] is not None:
        values = np.maximum(values, recipe["floor"])
    return values


def generate_mock(path: str | Path = DEFAULT_PATH, seed: int = SEED) -> pd.DataFrame:
    """Generate the mock dataset, write it to ``path`` and return it."""
    rng = np.random.default_rng(seed)
    index = pd.date_range(START, END, freq="MS")
    frames = []
    for (region, variable), recipe in RECIPES.items():
        values = _make_series(index, recipe, rng)
        n_nan = max(1, int(round(NAN_FRACTION * len(values))))
        values[rng.choice(len(values), size=n_nan, replace=False)] = np.nan
        frames.append(
            pd.DataFrame(
                {
                    "date": index.strftime("%Y-%m-%d"),
                    "region": region,
                    "variable": variable,
                    "value": np.round(values, 4),
                    "unit": recipe["unit"],
                }
            )
        )
    df = pd.concat(frames, ignore_index=True)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return df


if __name__ == "__main__":
    out = generate_mock()
    print(f"Wrote {len(out)} rows to {DEFAULT_PATH}")
