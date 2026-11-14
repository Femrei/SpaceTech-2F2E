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
    # Mock cases following D.md; D will rewrite the stories from the real results.
    "cases": [
        {"id": "konya_drying", "title": "Case 1: Is Konya drying out?",
         "story": "Farmers in the Konya plain say wells must be drilled deeper every year. "
                  "Is the soil itself getting drier, or is it just a few bad years?",
         "region_id": "konya", "variable_id": "soil_moisture", "compare_region_id": None},
        {"id": "van_heating", "title": "Case 2: Is Lake Van's basin heating up?",
         "story": "High, cold and remote, the Lake Van basin seems far from everything. "
                  "Has 25 years of satellite data picked up a warming signal here?",
         "region_id": "van", "variable_id": "temp", "compare_region_id": None},
        {"id": "opposite_stories", "title": "Case 3: Same country, opposite stories?",
         "story": "The Konya plain and the Eastern Black Sea coast are only a few hundred km apart, "
                  "yet their climates could hardly be more different. Is rain changing the same way in both?",
         "region_id": "konya", "variable_id": "precip", "compare_region_id": "black_sea"},
        {"id": "rain_or_heat", "title": "Case 4: Rain or heat - who's the culprit?",
         "story": "If the soil is drying, there are two usual suspects: less rain or more heat. "
                  "Start with the rain, then follow the clues.",
         "region_id": "konya", "variable_id": "precip", "compare_region_id": None},
    ],
}

THEMES = {
    "drought": "Is it getting drier?",
    "warming": "Is it getting hotter?",
    "water": "What's happening to water?",
}


# Değişken, bölge, sözlük ve vaka bilgilerinin hepsini (katalog) döndürür.
def load_catalog() -> dict:
    return _CATALOG


# id'si verilen değişkenin bilgilerini döndürür; bulunamazsa KeyError.
def get_variable(variable_id: str) -> dict:
    for v in _CATALOG["variables"]:
        if v["id"] == variable_id:
            return v
    raise KeyError(variable_id)


# id'si verilen bölgenin bilgilerini döndürür; bulunamazsa KeyError.
def get_region(region_id: str) -> dict:
    for r in _CATALOG["regions"]:
        if r["id"] == region_id:
            return r
    raise KeyError(region_id)


# Tema başına önerilerin sırası (en iyi öneri ilk) ve her değişken için gerekçe cümlesi.
_THEME_ORDER = {
    "drought": [("soil_moisture", "konya"), ("precip", "konya"), ("temp", "konya"),
                ("soil_moisture", "van"), ("precip", "van")],
    "warming": [("temp", "van"), ("temp", "konya"), ("temp", "black_sea"), ("soil_moisture", "konya")],
    "water": [("precip", "black_sea"), ("precip", "konya"), ("soil_moisture", "konya"),
              ("soil_moisture", "van")],
}
_REASONS = {
    "soil_moisture": "Soil moisture is one of the first places drought shows up.",
    "precip": "Rain and snow are where the water comes from: less of them can mean drier land.",
    "temp": "Warmer air dries soil faster and pulls more water out of plants and lakes.",
}


# Seçilen temaya (ör. 'drought') uygun değişken + bölge önerilerini, en iyisi
# ilk sırada olacak şekilde, her biri için bir gerekçe cümlesiyle listeler.
def suggest(theme: str) -> list[dict]:
    return [{"variable_id": v, "region_id": r, "reason": _REASONS[v]}
            for v, r in _THEME_ORDER[theme]]


# Terim sözlüğünü döndürür (terim -> sade açıklama).
def glossary() -> dict:
    return _CATALOG["glossary"]


# Hazır dedektif vakalarını (Case Files) listeler.
def get_cases() -> list[dict]:
    return _CATALOG["cases"]


# Kural tablosu: (değişken, durum) -> bir sonraki adım cümlesi.
# Durum: "up" = anlamlı artış, "down" = anlamlı azalış, "flat" = anlamlı trend yok.
_HINTS = {
    ("soil_moisture", "down"): "🕵️ Clue found! Soil is drying. Is it less rain, or more heat? Check precipitation next.",
    ("soil_moisture", "up"): "The soil is getting wetter. Does more rain explain it? Check precipitation.",
    ("soil_moisture", "flat"): "No significant trend yet. Try comparing with the Eastern Black Sea, or ask whether 25 years is long enough.",
    ("precip", "down"): "🕵️ Rain is decreasing. Is the soil feeling it? Check soil moisture next.",
    ("precip", "up"): "More rain here. Is the soil getting wetter too? Check soil moisture.",
    ("precip", "flat"): "Rain isn't clearly dropping, so what else could dry the soil? Try temperature.",
    ("temp", "up"): "🕵️ It's getting warmer. Warmer air dries soil faster: check soil moisture next.",
    ("temp", "down"): "Cooling here, that's unusual! Check precipitation for the full picture.",
    ("temp", "flat"): "No clear warming signal yet. Try the same question in another region.",
}


# Sonuca göre kullanıcıya bir sonraki adımı öneren dedektif cümlesi döndürür
# (yukarıdaki kural tablosundan: değişken x yön x anlamlılık).
def next_step_hint(result: dict, variable_id: str, region_id: str) -> str:
    if not result["significant"]:
        state = "flat"
    else:
        state = "up" if result["direction"] == "increasing" else "down"
    return _HINTS.get((variable_id, state), "Try another variable or region to keep investigating.")
