import numpy as np
import pandas as pd
import pymannkendall as mk
import pytest

from src.trend import (
    COMPARE_KEYS,
    RESULT_KEYS,
    analyze_trend,
    compare_trends,
    interpret,
)

INDEX = pd.date_range("2001-01-01", "2025-12-01", freq="MS")  # 300 months
YEARS = np.arange(len(INDEX)) / 12.0


def make_series(trend_per_decade=0.0, noise=0.1, amp=0.0, mean=10.0, seed=0, index=INDEX):
    rng = np.random.default_rng(seed)
    years = np.arange(len(index)) / 12.0
    seasonal = amp * np.sin(2 * np.pi * index.month / 12)
    values = mean + seasonal + trend_per_decade / 10 * years + rng.normal(0, noise, len(index))
    return pd.Series(values, index=index)


def test_known_positive_trend_is_detected():
    s = make_series(trend_per_decade=0.5, noise=0.1, amp=2.0)
    r = analyze_trend(s)
    assert r["significant"] is True
    assert r["direction"] == "increasing"
    assert r["sen_slope_per_decade"] == pytest.approx(0.5, abs=0.05)
    assert r["slope_per_decade"] == pytest.approx(0.5, abs=0.05)
    assert r["ci_low"] < 0.5 < r["ci_high"]


def test_known_negative_trend_is_detected():
    s = make_series(trend_per_decade=-1.2, noise=0.5, amp=3.0)
    r = analyze_trend(s)
    assert r["significant"] is True
    assert r["direction"] == "decreasing"
    assert r["sen_slope_per_decade"] == pytest.approx(-1.2, abs=0.15)


def test_pure_noise_is_not_significant():
    s = make_series(trend_per_decade=0.0, noise=1.0, seed=123)
    r = analyze_trend(s)
    assert r["significant"] is False
    assert r["years_needed_estimate"] is None or r["years_needed_estimate"] > 25


def test_strong_seasonality_without_trend_is_not_significant():
    # Seasonal amplitude 50x the noise and a partial final year: naive tests on
    # the raw series would pick up a spurious trend from the seasonal cycle.
    idx = pd.date_range("2001-01-01", "2024-06-01", freq="MS")
    s = make_series(trend_per_decade=0.0, noise=0.2, amp=10.0, seed=7, index=idx)
    r = analyze_trend(s)
    assert r["significant"] is False
    assert abs(r["slope_per_decade"]) < 0.1
    # anomalies must have the seasonal cycle removed
    assert r["anomalies"].groupby(r["anomalies"].index.month).mean().abs().max() < 1e-9
    assert r["anomalies"].std() < 0.5


def test_nan_values_are_handled_and_kept_in_place():
    s = make_series(trend_per_decade=0.5, noise=0.1, amp=2.0)
    nan_pos = [0, 13, 100, 101, 299]
    s.iloc[nan_pos] = np.nan
    r = analyze_trend(s)
    assert r["n"] == len(s) - len(nan_pos)
    assert r["significant"] is True
    for key in ("anomalies", "trend_line"):
        assert r[key].index.equals(s.index)
        assert r[key].iloc[nan_pos].isna().all()
        assert r[key].drop(s.index[nan_pos]).notna().all()


def test_all_contract_keys_present():
    r = analyze_trend(make_series(trend_per_decade=0.3))
    assert set(RESULT_KEYS) <= set(r)
    c = compare_trends(r, r)
    assert set(COMPARE_KEYS) <= set(c)


def test_sen_slope_unit_conversion():
    # Exact trend of 0.5 units/decade, no noise -> Sen slope must be exactly 0.5/decade.
    s = make_series(trend_per_decade=0.5, noise=0.0, amp=3.0)
    r = analyze_trend(s)
    assert r["sen_slope_per_decade"] == pytest.approx(0.5, rel=1e-9)
    # Cross-check the conversion rule: non-seasonal Sen slope on monthly anomalies is
    # per month, so x 12 x 10 must give the same per-decade value.
    monthly = mk.original_test(r["anomalies"].dropna().to_numpy()).slope
    assert monthly * 12 * 10 == pytest.approx(0.5, rel=1e-6)


def test_percent_change_and_zero_mean():
    r = analyze_trend(make_series(trend_per_decade=1.0, noise=0.05, mean=20.0))
    # mean over 2001-2025 is ~21.25 (20 + half of the 2.5-unit rise)
    assert r["mean_value"] == pytest.approx(21.25, abs=0.05)
    assert r["percent_change_per_decade"] == pytest.approx(100 / 21.25, rel=0.02)
    s0 = make_series(trend_per_decade=1.0, noise=0.05, mean=0.0)
    s0 = s0 - s0.mean()  # mean exactly ~0
    assert analyze_trend(s0)["percent_change_per_decade"] is None


def test_too_short_series_raises():
    s = make_series().iloc[:23]
    with pytest.raises(ValueError, match="24"):
        analyze_trend(s)
    s = make_series().iloc[:40].copy()
    s.iloc[:20] = np.nan
    with pytest.raises(ValueError):
        analyze_trend(s)


def test_years_needed_only_when_not_significant():
    assert analyze_trend(make_series(trend_per_decade=0.5))["years_needed_estimate"] is None
    weak = analyze_trend(make_series(trend_per_decade=0.1, noise=2.0, seed=3))
    assert weak["significant"] is False
    assert weak["years_needed_estimate"] > 25


@pytest.mark.parametrize(
    "trend, noise, expected",
    [(0.8, 0.1, "increased"), (-0.8, 0.1, "decreased"), (0.0, 1.0, "no statistically significant trend")],
)
def test_interpret_cases(trend, noise, expected):
    r = analyze_trend(make_series(trend_per_decade=trend, noise=noise, seed=11))
    text = interpret(r, "soil_moisture", "the Konya Closed Basin")
    assert expected in text
    assert "Konya" in text and "2001" in text and "2025" in text
    for word in ("proves", "prove", "certain", "definitely"):
        assert word not in text.lower()


def test_compare_trends():
    up = analyze_trend(make_series(trend_per_decade=0.8))
    down = analyze_trend(make_series(trend_per_decade=-0.8))
    flat = analyze_trend(make_series(trend_per_decade=0.0, noise=1.0, seed=123))
    assert compare_trends(up, up) == {**compare_trends(up, up), "same_direction": True, "both_significant": True}
    c = compare_trends(up, down)
    assert c["same_direction"] is False and c["both_significant"] is True
    c = compare_trends(up, flat)
    assert c["both_significant"] is False
    assert "first" in c["summary"]


def test_n_years_and_ci_bracket_slope():
    r = analyze_trend(make_series(trend_per_decade=0.3))
    assert r["n_years"] == pytest.approx(25.0)
    assert r["ci_low"] <= r["slope_per_decade"] <= r["ci_high"]


def test_interpret_temp_has_no_percent():
    r = analyze_trend(make_series(trend_per_decade=0.5, noise=0.2, mean=11.0))
    text = interpret(r, "temp", "the Konya Closed Basin")
    assert "°C per decade" in text
    assert "%" not in text


def test_mock_data_matches_shared_format(tmp_path):
    from src.mock_data import generate_mock

    df = generate_mock(tmp_path / "all_series.csv")
    assert list(df.columns) == ["date", "region_id", "variable_id", "value"]
    assert len(df) == 2700
    pairs = df.groupby(["region_id", "variable_id"]).size()
    assert len(pairs) == 9 and (pairs == 300).all()
    assert df["value"].isna().any()

    # round-trip the same way A's load_series does (asfreq('MS')) and analyze every series
    back = pd.read_csv(tmp_path / "all_series.csv", parse_dates=["date"])
    for (region, var), g in back.groupby(["region_id", "variable_id"]):
        s = g.set_index("date")["value"].asfreq("MS")
        assert len(s) == 300
        r = analyze_trend(s)
        assert set(RESULT_KEYS) <= set(r)
        assert interpret(r, var, region)
