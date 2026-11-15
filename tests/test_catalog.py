"""Validation of data/catalog.json and src/detective.py (D).

Run from the repo root:  python -m pytest -q
"""
from __future__ import annotations

import itertools
import json
import re

import pytest

from src.detective import (
    CATALOG_PATH,
    THEMES,
    CONTEXT_KEYS,
    get_cases,
    get_context,
    get_region,
    get_variable,
    glossary,
    load_catalog,
    next_step,
    next_step_hint,
    suggest,
)
from src.trend import VARIABLE_LABELS

# Shared IDs (must match A's process_giovanni.py and B's mock_data.py)
REGION_IDS = {"konya", "van", "black_sea"}
VARIABLE_IDS = {"precip", "soil_moisture", "temp"}
THEME_IDS = {"drought", "warming", "water"}
EXPECTED_DATASETS = {
    "precip": ("GPM_3IMERGM", "precipitation"),
    "soil_moisture": ("GLDAS_NOAH025_M", "SoilMoi0_10cm_inst"),
    "temp": ("M2TMNXSLV", "T2M"),
}
DIRECTIONS = ("increasing", "decreasing", "no change")
# Terms shown on the result card; each needs a glossary entry
REQUIRED_TERMS = {
    "trend", "anomaly", "seasonal cycle", "p-value", "statistically significant",
    "Mann-Kendall test", "Sen's slope", "confidence interval", "per decade", "area-averaged",
}

VARIABLE_FIELDS = {"id", "name", "short_description", "long_description", "dataset",
                   "dataset_variable", "source", "unit", "period", "themes"}
REGION_FIELDS = {"id", "name", "name_in_text", "bbox", "lat", "lon", "description", "teaser", "themes",
                 "compare_with"}
CASE_FIELDS = {"id", "title", "story", "region_id", "variable_id", "compare_region_id", "chain"}
SOURCES_PATH = CATALOG_PATH.parent / "SOURCES.md"


def _sources_bboxes() -> dict[str, tuple[float, ...]]:
    """region_id -> (W, S, E, N) as listed in A's data/SOURCES.md."""
    rows = re.findall(r"`(\w+?)__\w+\.csv` \| ([-\d.,]+) \|", SOURCES_PATH.read_text(encoding="utf-8"))
    out: dict[str, tuple[float, ...]] = {}
    for region_id, bbox in rows:
        values = tuple(float(x) for x in bbox.split(","))
        assert out.setdefault(region_id, values) == values, f"{region_id}: bbox differs between files"
    return out


def _result(direction: str, significant: bool) -> dict:
    return {"direction": direction, "significant": significant}


# --------------------------------------------------------------------------- #
# catalog.json structure
# --------------------------------------------------------------------------- #
def test_catalog_is_valid_json_utf8():
    json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def test_ids_match_shared_ids():
    cat = load_catalog()
    assert {v["id"] for v in cat["variables"]} == VARIABLE_IDS
    assert {r["id"] for r in cat["regions"]} == REGION_IDS
    assert {t["id"] for t in cat["themes"]} == THEME_IDS
    assert set(THEMES) == THEME_IDS


@pytest.mark.parametrize("variable_id", sorted(VARIABLE_IDS))
def test_variable_entries(variable_id):
    v = get_variable(variable_id)
    assert VARIABLE_FIELDS <= set(v)
    for field in ("name", "short_description", "long_description", "source"):
        assert v[field].strip()
    assert (v["dataset"], v["dataset_variable"]) == EXPECTED_DATASETS[variable_id]
    # same unit string as B's interpret() text
    assert v["unit"] == VARIABLE_LABELS[variable_id][1]
    assert re.fullmatch(r"\d{4}-\d{2}", v["period"]["start"])
    assert re.fullmatch(r"\d{4}-\d{2}", v["period"]["end"])
    assert v["themes"] and set(v["themes"]) <= THEME_IDS


@pytest.mark.parametrize("variable_id", sorted(VARIABLE_IDS))
def test_variable_period_matches_data(variable_id):
    # period = first..last month with a value in A's processed data, in every region
    from src.data_loader import load_series

    period = get_variable(variable_id)["period"]
    for region_id in sorted(REGION_IDS):
        valid = load_series(region_id, variable_id).dropna().index
        assert valid.min().strftime("%Y-%m") == period["start"], region_id
        assert valid.max().strftime("%Y-%m") == period["end"], region_id


def test_region_bboxes_match_sources_md():
    sources = _sources_bboxes()
    assert set(sources) == REGION_IDS
    for region_id, (west, south, east, north) in sources.items():
        b = get_region(region_id)["bbox"]
        assert (b["west"], b["south"], b["east"], b["north"]) == pytest.approx((west, south, east, north)), region_id


@pytest.mark.parametrize("region_id", sorted(REGION_IDS))
def test_region_entries(region_id):
    r = get_region(region_id)
    assert REGION_FIELDS <= set(r)
    b = r["bbox"]
    assert -180 <= b["west"] < b["east"] <= 180
    assert -90 <= b["south"] < b["north"] <= 90
    assert r["lat"] == pytest.approx((b["south"] + b["north"]) / 2)
    assert r["lon"] == pytest.approx((b["west"] + b["east"]) / 2)
    assert r["themes"] and set(r["themes"]) <= THEME_IDS
    assert r["compare_with"] in REGION_IDS - {region_id}


def test_theme_reasons_match_variable_themes():
    for theme in load_catalog()["themes"]:
        listed = [r["variable_id"] for r in theme["reasons"]]
        assert len(listed) == len(set(listed))
        tagged = {v["id"] for v in load_catalog()["variables"] if theme["id"] in v["themes"]}
        assert set(listed) == tagged, theme["id"]


def test_glossary_covers_result_card_terms():
    g = glossary()
    assert REQUIRED_TERMS <= set(g)
    assert all(text.strip() for text in g.values())


def test_cases_reference_known_ids():
    cases = get_cases()
    assert cases
    assert len({c["id"] for c in cases}) == len(cases)
    for c in cases:
        assert CASE_FIELDS <= set(c)
        assert c["region_id"] in REGION_IDS
        assert c["variable_id"] in VARIABLE_IDS
        assert c["compare_region_id"] in REGION_IDS | {None}
        assert c["compare_region_id"] != c["region_id"]
        if c["chain"] is not None:
            assert len(c["chain"]) >= 2 and set(c["chain"]) <= VARIABLE_IDS
            assert c["chain"][0] == c["variable_id"]


def test_case_chains_follow_real_data_hints():
    # Following the "follow the clue" button on the real data walks the case's chain
    from src.data_loader import load_series
    from src.trend import analyze_trend

    for c in get_cases():
        if c["chain"] is None:
            continue
        for here, expected in zip(c["chain"], c["chain"][1:]):
            step = next_step(analyze_trend(load_series(c["region_id"], here)), here, c["region_id"])
            assert (step["variable_id"], step["region_id"]) == (expected, c["region_id"]), (c["id"], here)


# --------------------------------------------------------------------------- #
# detective.py behaviour
# --------------------------------------------------------------------------- #
def test_unknown_ids_raise_keyerror():
    with pytest.raises(KeyError):
        get_variable("ndvi")
    with pytest.raises(KeyError):
        get_region("mars")
    with pytest.raises(KeyError):
        suggest("flooding")


@pytest.mark.parametrize("theme", sorted(THEME_IDS))
def test_every_theme_has_suggestions(theme):
    out = suggest(theme)
    assert out
    for s in out:
        assert set(s) == {"variable_id", "region_id", "reason"}
        assert s["variable_id"] in VARIABLE_IDS and s["region_id"] in REGION_IDS
        assert s["reason"].strip()
    assert len({(s["variable_id"], s["region_id"]) for s in out}) == len(out)


def test_drought_suggestions():
    out = suggest("drought")
    assert len(out) >= 2
    assert (out[0]["variable_id"], out[0]["region_id"]) == ("soil_moisture", "konya")


@pytest.mark.parametrize(
    "variable_id,region_id,direction,significant",
    list(itertools.product(sorted(VARIABLE_IDS), sorted(REGION_IDS), DIRECTIONS, (True, False))),
)
def test_next_step_for_every_combination(variable_id, region_id, direction, significant):
    step = next_step(_result(direction, significant), variable_id, region_id)
    assert step["text"].strip()
    assert "{" not in step["text"] and "}" not in step["text"]
    if step["variable_id"] is not None:
        assert step["variable_id"] in VARIABLE_IDS
        assert step["region_id"] in REGION_IDS
        # a follow-up must lead somewhere new
        assert (step["variable_id"], step["region_id"]) != (variable_id, region_id)
    assert next_step_hint(_result(direction, significant), variable_id, region_id) == step["text"]


def test_next_step_examples():
    step = next_step(_result("decreasing", True), "soil_moisture", "konya")
    assert "Clue found" in step["text"] and "Konya Closed Basin" in step["text"]
    assert (step["variable_id"], step["region_id"]) == ("precip", "konya")

    step = next_step(_result("decreasing", False), "precip", "konya")
    assert step["variable_id"] == "temp"

    step = next_step(_result("increasing", False), "temp", "konya")
    assert step["region_id"] == "black_sea"


def test_significant_but_no_change_is_handled():
    # B's seasonal Sen slope can be exactly 0 while the test is significant
    step = next_step(_result("no change", True), "precip", "van")
    assert "about zero" in step["text"]
    assert step["variable_id"] is None


def test_hints_table_ends_with_catch_all():
    last = load_catalog()["hints"][-1]
    assert (last["variable_id"], last["direction"], last["significant"]) == ("*", "*", "*")


def test_works_with_real_analyze_trend_output():
    import numpy as np
    import pandas as pd

    from src.trend import analyze_trend

    idx = pd.date_range("2001-01-01", "2025-12-01", freq="MS")
    rng = np.random.default_rng(0)
    s = pd.Series(20 + 5 * np.cos(2 * np.pi * idx.month / 12) - 0.012 * np.arange(len(idx))
                  + rng.normal(0, 0.5, len(idx)), index=idx)
    hint = next_step_hint(analyze_trend(s), "soil_moisture", "konya")
    assert "drying" in hint


# --------------------------------------------------------------------------- #
# "What does this mean?" context texts (variables[].context)
# --------------------------------------------------------------------------- #
# Phrases that would claim a cause instead of describing what a trend can mean
CAUSAL_PHRASES = ("caused by", "is causing", "proves", "due to", "because of climate change")


@pytest.mark.parametrize("variable_id", sorted(VARIABLE_IDS))
def test_variable_context_texts(variable_id):
    context = get_variable(variable_id)["context"]
    assert set(context) == set(CONTEXT_KEYS) | {"sources"}
    for key in CONTEXT_KEYS:
        text = context[key]
        assert isinstance(text, str) and 40 <= len(text) <= 400, f"{variable_id}.{key}: length {len(text)}"
        assert text.count(". ") <= 1, f"{variable_id}.{key}: keep it to 1-2 sentences"
        lowered = text.lower()
        assert not any(p in lowered for p in CAUSAL_PHRASES), f"{variable_id}.{key}: causal wording"


@pytest.mark.parametrize("variable_id", sorted(VARIABLE_IDS))
def test_variable_context_sources(variable_id):
    sources = get_variable(variable_id)["context"]["sources"]
    assert sources, f"{variable_id}: context needs at least one source"
    for source in sources:
        assert set(source) == {"title", "url"}
        assert source["title"].strip()
        assert source["url"].startswith("https://")


@pytest.mark.parametrize(
    ("direction", "significant", "expected"),
    [
        ("increasing", True, "increasing"),
        ("decreasing", True, "decreasing"),
        ("increasing", False, "no_clear_trend"),
        ("decreasing", False, "no_clear_trend"),
        ("no change", True, "no_clear_trend"),
        ("no change", False, "no_clear_trend"),
    ],
)
@pytest.mark.parametrize("variable_id", sorted(VARIABLE_IDS))
def test_get_context_picks_text(variable_id, direction, significant, expected):
    out = get_context(_result(direction, significant), variable_id)
    context = get_variable(variable_id)["context"]
    assert out["key"] == expected
    assert out["text"] == context[expected]
    assert out["sources"] == context["sources"]


def test_get_context_unknown_variable_raises():
    with pytest.raises(KeyError):
        get_context(_result("increasing", True), "wind")
