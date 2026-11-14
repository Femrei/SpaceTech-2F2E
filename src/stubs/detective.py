# TEMP STUB — will be replaced by D (src/detective.py + data/catalog.json)
"""Stand-in for D's catalog and detective logic.

The catalog lives inline here (not in data/catalog.json, which D owns).
Bounding boxes are rough placeholders: D/A will provide the verified ones.
"""
from __future__ import annotations

_CATALOG = {
    "variables": [
        {
            "id": "precip", "name": "Precipitation", "unit": "mm/month",
            "dataset": "GPM_3IMERGM", "period": "2001-01 to 2025-12",
            "short_description": "How much rain and snow falls each month.",
            "long_description": "Placeholder text (D will write this).",
            "themes": ["drought", "water"],
        },
        {
            "id": "soil_moisture", "name": "Surface soil moisture", "unit": "kg/m²",
            "dataset": "GLDAS_NOAH025_M", "period": "2001-01 to 2025-12",
            "short_description": "How wet the top 10 cm of soil is: the water plants can easily reach.",
            "long_description": "Placeholder text (D will write this).",
            "themes": ["drought", "water"],
        },
        {
            "id": "temp", "name": "Air temperature (2 m)", "unit": "°C",
            "dataset": "M2TMNXSLV", "period": "2001-01 to 2025-12",
            "short_description": "The average air temperature 2 metres above the ground.",
            "long_description": "Placeholder text (D will write this).",
            "themes": ["warming", "drought"],
        },
    ],
    "regions": [
        {"id": "konya", "name": "Konya Closed Basin", "bbox": [31.5, 36.8, 34.5, 39.0],
         "lat": 37.9, "lon": 33.0, "description": "Placeholder text (D will write this)."},
        {"id": "van", "name": "Lake Van Basin", "bbox": [42.0, 38.0, 44.0, 39.5],
         "lat": 38.75, "lon": 43.0, "description": "Placeholder text (D will write this)."},
        {"id": "black_sea", "name": "Eastern Black Sea", "bbox": [37.5, 40.5, 42.0, 41.5],
         "lat": 41.0, "lon": 39.75, "description": "Placeholder text (D will write this)."},
    ],
    "glossary": {
        "trend": "The long-term direction a quantity is moving in, once the ups and downs are averaged out.",
        "anomaly": "How far a month is from what is normal for that calendar month.",
        "seasonal cycle": "The regular up-and-down pattern that repeats every year.",
        "p-value": "How likely a trend this strong would appear by pure chance if nothing were really changing. Below 0.05 = significant.",
        "statistically significant": "Unlikely to be explained by random variation alone (here: p < 0.05).",
        "Mann-Kendall test": "A test that checks whether values tend to keep going up (or down) over time, without assuming a straight line.",
        "Sen's slope": "A robust estimate of the trend: the median of the slopes between all pairs of points.",
        "confidence interval": "The range the true trend probably lies in (95% confidence).",
        "per decade": "The change over 10 years at the current rate.",
        "area-averaged": "One value per month, averaged over the whole region.",
    },
    "cases": [
        {"id": "konya_drying", "title": "Case 1: Is Konya drying out?",
         "story": "Placeholder story (D will write this).",
         "region_id": "konya", "variable_id": "soil_moisture", "compare_region_id": None},
    ],
}

THEMES = {
    "drought": "Is it getting drier?",
    "warming": "Is it getting hotter?",
    "water": "What's happening to water?",
}


def load_catalog() -> dict:
    return _CATALOG


def get_variable(variable_id: str) -> dict:
    for v in _CATALOG["variables"]:
        if v["id"] == variable_id:
            return v
    raise KeyError(variable_id)


def get_region(region_id: str) -> dict:
    for r in _CATALOG["regions"]:
        if r["id"] == region_id:
            return r
    raise KeyError(region_id)


def suggest(theme: str) -> list[dict]:
    return [
        {"variable_id": v["id"], "region_id": r["id"],
         "reason": f"{v['name']} is a good place to look for '{THEMES[theme]}'"}
        for v in _CATALOG["variables"] if theme in v["themes"]
        for r in _CATALOG["regions"]
    ]


def glossary() -> dict:
    return _CATALOG["glossary"]


def get_cases() -> list[dict]:
    return _CATALOG["cases"]


def next_step_hint(result: dict, variable_id: str, region_id: str) -> str:
    if not result["significant"]:
        return "No significant trend yet: try another region, or ask whether 25 years is long enough."
    return "🕵️ Clue found! Check a related variable next."
