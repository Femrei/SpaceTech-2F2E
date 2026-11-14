# TEMP STUB — will be replaced by B (src/trend.py)
"""Stand-in for B's trend module.

Does a real-but-simple analysis (monthly-climatology anomalies, OLS on the
anomalies, Mann-Kendall on the anomalies) so the UI shows plausible numbers.
B's module is the scientific source of truth; do not cite these numbers.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

try:
    import pymannkendall as mk
except ImportError:  # pragma: no cover
    mk = None


def _decimal_years(index: pd.DatetimeIndex) -> np.ndarray:
    return (index.year + (index.month - 1) / 12).to_numpy(dtype=float)


def analyze_trend(series: pd.Series) -> dict:
    s = series.astype(float)
    valid = s.dropna()
    if len(valid) < 24:
        raise ValueError(f"Not enough data: {len(valid)} valid months (need at least 24).")

    anomalies = s - s.groupby(s.index.month).transform("mean")
    a = anomalies.dropna()
    t = _decimal_years(a.index)
    lr = stats.linregress(t, a.to_numpy())
    n = len(a)
    t_crit = stats.t.ppf(0.975, n - 2)

    trend_line = pd.Series(lr.intercept + lr.slope * _decimal_years(s.index), index=s.index)
    trend_line[s.isna()] = np.nan

    if mk is not None:
        mk_res = mk.original_test(a.to_numpy())
        mk_p, sen_per_decade = float(mk_res.p), float(mk_res.slope) * 12 * 10
    else:
        mk_p, sen_per_decade = float(lr.pvalue), float(lr.slope) * 10

    slope_dec = float(lr.slope) * 10
    mean_value = float(valid.mean())
    significant = mk_p < 0.05
    years_needed = None
    if not significant and lr.slope != 0:
        n_needed = n * (t_crit * lr.stderr / abs(lr.slope)) ** (2 / 3)
        years_needed = int(np.ceil(n_needed / 12))

    return {
        "anomalies": anomalies,
        "trend_line": trend_line,
        "slope_per_decade": slope_dec,
        "ci_low": float(lr.slope - t_crit * lr.stderr) * 10,
        "ci_high": float(lr.slope + t_crit * lr.stderr) * 10,
        "ols_p": float(lr.pvalue),
        "mk_p": mk_p,
        "sen_slope_per_decade": sen_per_decade,
        "significant": bool(significant),
        "direction": "increasing" if slope_dec > 0 else "decreasing",
        "percent_change_per_decade": (
            slope_dec / abs(mean_value) * 100 if abs(mean_value) > 1e-9 else None
        ),
        "mean_value": mean_value,
        "n_years": int(valid.index.year.nunique()),
        "start_year": int(valid.index.year.min()),
        "end_year": int(valid.index.year.max()),
        "years_needed_estimate": years_needed,
    }


def interpret(result: dict, variable: dict, region: dict) -> str:
    unit = variable["unit"]
    verb = "increased" if result["direction"] == "increasing" else "decreased"
    text = (
        f"{variable['name']} in the {region['name']} has {verb} by about "
        f"{abs(result['slope_per_decade']):.2f} {unit} per decade between "
        f"{result['start_year']} and {result['end_year']}. "
    )
    if result["significant"]:
        text += (f"This trend is statistically significant (Mann-Kendall p = {result['mk_p']:.3f}), "
                 "so it is unlikely to be just random year-to-year variation.")
    else:
        text += f"This is not statistically significant yet (Mann-Kendall p = {result['mk_p']:.2f})."
        if result["years_needed_estimate"]:
            text += (f" At the current rate, roughly {result['years_needed_estimate']} years "
                     "of data might be needed to tell.")
    return text


def compare_trends(result_a: dict, result_b: dict, region_a: dict, region_b: dict) -> dict:
    same = result_a["direction"] == result_b["direction"]
    both = result_a["significant"] and result_b["significant"]
    if same:
        summary = f"Both {region_a['name']} and {region_b['name']} are {result_a['direction']}."
    else:
        summary = (f"Opposite stories: {region_a['name']} is {result_a['direction']} while "
                   f"{region_b['name']} is {result_b['direction']}.")
    return {"same_direction": same, "both_significant": both, "summary": summary}
