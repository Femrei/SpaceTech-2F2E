"""Synthetic stand-in for ``data/processed/all_series.csv`` until A's real Giovanni data is ready.

Run (from the repo root):
    python -m src.mock_data

Output format (identical to what ``scripts/process_giovanni.py`` will write, so
nobody has to change code when A swaps in the real file):

    date,region_id,variable_id,value
    2001-01-01,konya,precip,41.27
    ...

* 3 regions x 3 variables = 9 series, each exactly 300 monthly rows
  (2001-01 .. 2025-12, dates normalised to ``YYYY-MM-01``)
* units as in the shared table: precip mm/month, soil_moisture kg/m², temp °C
* ~1% of values are NaN (row kept, value empty) so everyone tests with gaps
* fixed seed -> reproducible

Each series = climatological mean + seasonal cycle + linear trend + noise.
The trends are invented (NOT real findings); they are chosen so that the
mock data exercises every UI state: significant decrease, significant
increase and no significant trend, plus an opposite-sign pair
(konya vs. black_sea precipitation) for the Compare tab.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PATH = ROOT / "data" / "processed" / "all_series.csv"

START = "2001-01-01"
END = "2025-12-01"
N_MONTHS = 300
NAN_FRACTION = 0.01
SEED = 42

REGIONS = ("konya", "van", "black_sea")
VARIABLES = ("precip", "soil_moisture", "temp")
UNITS = {"precip": "mm/month", "soil_moisture": "kg/m²", "temp": "°C"}

# mean, seasonal amplitude, month of seasonal peak, trend per decade, noise std, lower bound
RECIPES: dict[tuple[str, str], dict] = {
    # Konya: semi-arid, winter/spring rain, hot dry summers
    ("konya", "precip"):        dict(mean=27.0,  amp=18.0, peak=1,  trend=-2.0, noise=8.0,  floor=0.0),
    ("konya", "soil_moisture"): dict(mean=24.0,  amp=6.0,  peak=3,  trend=-1.2, noise=1.5,  floor=0.0),
    ("konya", "temp"):          dict(mean=11.5,  amp=11.5, peak=7,  trend=0.5,  noise=1.0,  floor=None),
    # Van: high plateau, cold winters, spring precipitation maximum
    ("van", "precip"):          dict(mean=35.0,  amp=15.0, peak=4,  trend=0.0,  noise=10.0, floor=0.0),
    ("van", "soil_moisture"):   dict(mean=27.0,  amp=7.0,  peak=4,  trend=-0.3, noise=2.0,  floor=0.0),
    ("van", "temp"):            dict(mean=8.0,   amp=13.0, peak=7,  trend=0.6,  noise=1.2,  floor=None),
    # Eastern Black Sea: very wet all year, autumn maximum
    ("black_sea", "precip"):        dict(mean=170.0, amp=60.0, peak=10, trend=12.0, noise=35.0, floor=0.0),
    ("black_sea", "soil_moisture"): dict(mean=33.0,  amp=3.0,  peak=12, trend=0.0,  noise=1.5,  floor=0.0),
    ("black_sea", "temp"):          dict(mean=13.5,  amp=8.5,  peak=8,  trend=0.3,  noise=0.9,  floor=None),
}


def _make_series(index: pd.DatetimeIndex, recipe: dict, rng: np.random.Generator) -> np.ndarray:
    month = np.asarray(index.month)
    years = np.arange(len(index)) / 12.0
    seasonal = recipe["amp"] * np.cos(2 * np.pi * (month - recipe["peak"]) / 12.0)
    trend = recipe["trend"] / 10.0 * years
    noise = rng.normal(0.0, recipe["noise"], size=len(index))
    values = recipe["mean"] + seasonal + trend + noise
    if recipe["floor"] is not None:
        values = np.maximum(values, recipe["floor"])
    return values


def generate_mock(path: str | Path = DEFAULT_PATH, seed: int = SEED) -> pd.DataFrame:
    """Generate the mock dataset, write it to ``path`` (CSV) and return it."""
    rng = np.random.default_rng(seed)
    index = pd.date_range(START, END, freq="MS")
    assert len(index) == N_MONTHS
    frames = []
    for region in REGIONS:
        for variable in VARIABLES:
            values = _make_series(index, RECIPES[(region, variable)], rng)
            n_nan = max(1, int(round(NAN_FRACTION * N_MONTHS)))
            values[rng.choice(N_MONTHS, size=n_nan, replace=False)] = np.nan
            frames.append(
                pd.DataFrame(
                    {
                        "date": index.strftime("%Y-%m-%d"),
                        "region_id": region,
                        "variable_id": variable,
                        "value": np.round(values, 4),
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
    print(f"Wrote {len(out)} rows ({out.groupby(['region_id', 'variable_id']).ngroups} series) to {DEFAULT_PATH}")
