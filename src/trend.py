"""Trend statistics for monthly climate / land-surface series.

Public API (contract used by C's chart/result card and D's ``next_step_hint``;
do not rename keys without telling them):

    analyze_trend(series)                    -> dict  (keys: RESULT_KEYS)
    interpret(result, variable, region)      -> str
    compare_trends(result_a, result_b)       -> dict  (keys: COMPARE_KEYS)

Input: the output of A's ``data_loader.load_series(region_id, variable_id)``:
a monthly ``pd.Series`` with a ``DatetimeIndex`` (freq 'MS'); NaNs allowed.

``interpret`` takes a variable id (``precip`` / ``soil_moisture`` / ``temp``)
and a human-readable region name (e.g. D's ``get_region(id)["name"]``).
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pymannkendall as mk
from scipy import stats

ALPHA = 0.05
MIN_VALID_POINTS = 24
MONTHS_PER_YEAR = 12

RESULT_KEYS = (
    "n",                         # number of valid (non-NaN) monthly values
    "n_years",                   # length of the record in years (first..last valid month)
    "start",                     # first date with data (pd.Timestamp)
    "end",                       # last date with data (pd.Timestamp)
    "mean_value",                # mean of the valid values (series units)
    "slope_per_decade",          # OLS slope on anomalies, units / 10 yr (= slope of trend_line)
    "ci_low",                    # 95% CI lower bound of the OLS slope, units / 10 yr
    "ci_high",                   # 95% CI upper bound of the OLS slope, units / 10 yr
    "ols_p",                     # OLS p-value (assumes independent residuals)
    "sen_slope_per_decade",      # Sen's slope from the seasonal MK test, units / 10 yr
    "percent_change_per_decade", # sen_slope_per_decade / |mean_value| * 100 (None if mean ~ 0)
    "mk_p",                      # p-value of the primary test (seasonal Mann-Kendall)
    "mk_tau",                    # Kendall's tau of the primary test
    "significant",               # mk_p < ALPHA
    "direction",                 # "increasing" | "decreasing" | "no change" (sign of Sen's slope)
    "years_needed_estimate",     # rough total record length (years) for significance; None if significant
    "anomalies",                 # pd.Series, same index as input, NaNs kept in place
    "trend_line",                # pd.Series, OLS line in original units, same index as input, NaNs kept
    "method",                    # human-readable description of the primary test
)

COMPARE_KEYS = ("same_direction", "both_significant", "summary")


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _decimal_year(index: pd.DatetimeIndex) -> np.ndarray:
    """Decimal year at the start of each month (2001-01 -> 2001.0, 2001-07 -> 2001.5)."""
    return np.asarray(index.year + (index.month - 1) / MONTHS_PER_YEAR, dtype=float)


def _prepare(series: pd.Series) -> pd.Series:
    if not isinstance(series, pd.Series):
        raise TypeError("analyze_trend expects a pandas Series")
    if not isinstance(series.index, pd.DatetimeIndex):
        raise TypeError("series must have a DatetimeIndex")
    s = series.astype(float).sort_index()
    n_valid = int(s.notna().sum())
    if n_valid < MIN_VALID_POINTS:
        raise ValueError(
            f"Need at least {MIN_VALID_POINTS} valid monthly values for a trend analysis, got {n_valid}."
        )
    return s


def monthly_anomalies(series: pd.Series) -> pd.Series:
    """Subtract each calendar month's long-term mean (climatology). NaNs stay NaN."""
    return series - series.groupby(series.index.month).transform("mean")


def _regular_monthly(series: pd.Series) -> pd.Series:
    """Put the series on a regular month-start grid (missing months become NaN).

    The seasonal Mann-Kendall test groups values by position (every 12th value
    is the same season), so gaps in the index must be explicit NaNs.
    """
    s = series.copy()
    s.index = s.index.to_period("M").to_timestamp()
    s = s.groupby(level=0).mean()
    full = pd.date_range(s.index.min(), s.index.max(), freq="MS")
    return s.reindex(full)


# --------------------------------------------------------------------------- #
# main analysis
# --------------------------------------------------------------------------- #
def analyze_trend(series: pd.Series) -> dict:
    """Trend analysis of a monthly series.

    Steps
    -----
    1. **Anomalies**: subtract the monthly climatology
       ``s - s.groupby(s.index.month).transform('mean')``. NaNs remain in place;
       ``anomalies`` and ``trend_line`` keep the original index.
    2. **OLS** on the anomalies (NaNs dropped) with decimal year as the time
       axis (``scipy.stats.linregress``). Slope x 10 = units per decade.
       95% CI = ``slope +/- t_{0.975, n-2} * stderr`` (x 10).
       OLS assumes independent residuals, so its p-value is reported but not
       used for the significance decision.
    3. **Primary significance test: seasonal Mann-Kendall**
       (``pymannkendall.seasonal_test(series, period=12)``) on the *raw*
       monthly series. It compares each month only with the same calendar
       month in other years, so it is insensitive to the seasonal cycle, does
       not depend on the climatology estimate and, being rank-based, is robust
       to outliers and non-normal data (e.g. skewed precipitation).
       ``significant`` and ``mk_p`` come from this test.
    4. **Sen's slope** from the same seasonal test. Its ``slope`` is already in
       units per *year* (differences between the same month in different
       years), so x 10 gives units per decade. (For the non-seasonal
       ``original_test`` on monthly steps the factor would be x 12 x 10.)
    5. ``percent_change_per_decade`` = Sen slope per decade / |mean| x 100;
       ``None`` if the mean is ~0 (e.g. anomalies, temperatures near 0 degC).
    6. ``years_needed_estimate`` (only when not significant): a *rough* guess
       of the total record length needed for the current slope to become
       significant at the current noise level. Assumes the OLS stderr scales
       as n^(-3/2) (true for a linear trend with white noise):
       ``n_needed = n * (t_crit * stderr / |slope|)^(2/3)`` months, returned in
       years. It ignores autocorrelation and assumes the slope stays the same,
       so treat it as an order of magnitude only. ``None`` when the trend is
       already significant or the slope is exactly zero.

    Raises
    ------
    ValueError if fewer than 24 valid values remain after dropping NaNs.
    """
    s = _prepare(series)

    anomalies = monthly_anomalies(s)
    valid = anomalies.dropna()
    n = int(len(valid))
    t = _decimal_year(valid.index)

    # --- OLS on anomalies ---------------------------------------------------
    reg = stats.linregress(t, valid.to_numpy())
    t_crit = float(stats.t.ppf(1 - ALPHA / 2, n - 2))
    slope_dec = reg.slope * 10
    ci_half = t_crit * reg.stderr * 10

    mean_value = float(s.mean())
    # Anomalies average exactly 0, so the OLS line passes through (mean(t), 0);
    # adding the series mean puts it on the data in original units.
    t_all = _decimal_year(s.index)
    trend_line = pd.Series(mean_value + reg.slope * (t_all - t.mean()), index=s.index)
    trend_line[s.isna()] = np.nan

    # --- seasonal Mann-Kendall (primary test) -------------------------------
    regular = _regular_monthly(s)
    smk = mk.seasonal_test(regular.to_numpy(), period=MONTHS_PER_YEAR, alpha=ALPHA)
    mk_p = float(smk.p)
    significant = bool(mk_p < ALPHA)
    sen_dec = float(smk.slope) * 10  # seasonal slope is per year

    if sen_dec > 0:
        direction = "increasing"
    elif sen_dec < 0:
        direction = "decreasing"
    else:
        direction = "no change"

    if not math.isfinite(mean_value) or abs(mean_value) < 1e-9:
        pct = None
    else:
        pct = float(sen_dec / abs(mean_value) * 100)

    years_needed = None
    if not significant and reg.slope != 0 and reg.stderr > 0:
        n_needed = n * (t_crit * reg.stderr / abs(reg.slope)) ** (2 / 3)
        years_needed = float(max(n_needed, n) / MONTHS_PER_YEAR)

    start, end = valid.index.min(), valid.index.max()
    n_years = ((end.year - start.year) * MONTHS_PER_YEAR + end.month - start.month + 1) / MONTHS_PER_YEAR

    return {
        "n": n,
        "n_years": float(n_years),
        "start": start,
        "end": end,
        "mean_value": mean_value,
        "slope_per_decade": float(slope_dec),
        "ci_low": float(slope_dec - ci_half),
        "ci_high": float(slope_dec + ci_half),
        "ols_p": float(reg.pvalue),
        "sen_slope_per_decade": sen_dec,
        "percent_change_per_decade": pct,
        "mk_p": mk_p,
        "mk_tau": float(smk.Tau),
        "significant": significant,
        "direction": direction,
        "years_needed_estimate": years_needed,
        "anomalies": anomalies,
        "trend_line": trend_line,
        "method": "Seasonal Mann-Kendall test (period 12) with seasonal Sen's slope",
    }


# --------------------------------------------------------------------------- #
# text
# --------------------------------------------------------------------------- #
VARIABLE_LABELS = {
    "precip": ("Precipitation", "mm/month"),
    "soil_moisture": ("Surface soil moisture", "kg/m²"),
    "temp": ("Near-surface air temperature", "°C"),
}
# Variables on an interval scale (arbitrary zero) where "% change" has no meaning.
# analyze_trend still returns percent_change_per_decade; C should hide it for these.
NO_PERCENT_VARIABLES = {"temp"}


def _fmt(x: float) -> str:
    ax = abs(x)
    if ax == 0:
        return "0"
    if ax >= 10:
        return f"{ax:.1f}"
    if ax >= 0.1:
        return f"{ax:.2f}"
    return f"{ax:.2g}"


def _fmt_p(p: float) -> str:
    return "p < 0.001" if p < 0.001 else f"p = {p:.3f}"


def interpret(result: dict, variable: str, region: str) -> str:
    """Plain-English, cautious 2-3 sentence summary of an ``analyze_trend`` result."""
    label, unit = VARIABLE_LABELS.get(variable, (variable.replace("_", " ").capitalize(), ""))
    unit_txt = f" {unit}" if unit else ""
    years = f"between {result['start'].year} and {result['end'].year}"
    sen = result["sen_slope_per_decade"]
    pct = result["percent_change_per_decade"]
    # % of a °C value is meaningless (0 °C is an arbitrary zero), so skip it for temperature
    show_pct = pct is not None and variable not in NO_PERCENT_VARIABLES
    pct_txt = f" (≈{abs(pct):.1f}% per decade)" if show_pct else ""
    p_txt = _fmt_p(result["mk_p"])

    if result["significant"]:
        verb = "increased" if sen > 0 else "decreased"
        return (
            f"{label} in {region} has {verb} by about {_fmt(sen)}{unit_txt} per decade{pct_txt} {years}. "
            f"This trend is statistically significant (Mann-Kendall {p_txt}), meaning it is very unlikely "
            f"to be due to random year-to-year variation alone. "
            f"The test describes the change itself, not its cause."
        )

    if sen == 0:
        tendency = "shows no clear tendency"
    else:
        tendency = (
            f"shows a slight {'increase' if sen > 0 else 'decrease'} of about "
            f"{_fmt(sen)}{unit_txt} per decade{pct_txt}"
        )
    text = (
        f"{label} in {region} {tendency} {years}, but there is no statistically significant trend yet "
        f"(Mann-Kendall {p_txt}); the change cannot be distinguished from natural variability."
    )
    yn = result["years_needed_estimate"]
    if yn is not None:
        record = result["n_years"]
        if record < yn < 200:
            text += (
                f" At the current rate, roughly {yn:.0f} years of data in total might be needed "
                f"to detect it (a rough estimate; we currently have about {record:.0f})."
            )
        elif yn >= 200:
            text += " At the current rate, a much longer record would be needed to detect any trend."
    return text


def compare_trends(result_a: dict, result_b: dict) -> dict:
    """Compare two ``analyze_trend`` results (e.g. precipitation vs. soil moisture)."""
    da, db = result_a["direction"], result_b["direction"]
    sa, sb = result_a["significant"], result_b["significant"]
    same_direction = da == db and da != "no change"
    both_significant = bool(sa and sb)

    if both_significant and same_direction:
        summary = f"Both series show significant {da} trends over the period."
    elif both_significant:
        summary = f"Both trends are significant but point in opposite directions ({da} vs. {db})."
    elif sa or sb:
        sig, other = ("first", "second") if sa else ("second", "first")
        sig_dir = da if sa else db
        summary = (
            f"Only the {sig} series has a significant ({sig_dir}) trend; "
            f"the {other} shows no significant change yet."
        )
    else:
        summary = "Neither series shows a statistically significant trend yet."
    return {"same_direction": same_direction, "both_significant": both_significant, "summary": summary}
