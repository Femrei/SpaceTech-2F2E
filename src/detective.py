"""Detective layer: catalog lookups, theme-based suggestions and next-step hints.

All texts and rule tables live in ``data/catalog.json`` so that any frontend
(the React UI included) can read them directly; this module only implements the
small amount of logic on top of them. A TypeScript port of ``suggest`` and
``next_step`` needs nothing but the JSON.

Public API (used by the UI; do not change signatures without telling C):

    load_catalog()                                  -> dict
    get_variable(variable_id)                       -> dict   (KeyError if unknown)
    get_region(region_id)                           -> dict   (KeyError if unknown)
    THEMES                                          -> dict[theme_id, question]
    suggest(theme)                                  -> list[{"variable_id", "region_id", "reason"}]
    glossary()                                      -> dict[term, definition]
    next_step_hint(result, variable_id, region_id)  -> str
    next_step(result, variable_id, region_id)       -> {"text", "text_tr", "variable_id", "region_id"}
    get_context(result, variable_id)                -> {"key", "text", "text_tr", "sources"}

``result`` is the dict returned by B's ``trend.analyze_trend``; only its
``direction`` and ``significant`` keys are read.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

CATALOG_PATH = Path(__file__).resolve().parent.parent / "data/catalog.json"

WILDCARD = "*"


@lru_cache(maxsize=1)
def load_catalog() -> dict:
    """The parsed ``catalog.json``. Cached: treat the returned dict as read-only."""
    with CATALOG_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _by_id(section: str, item_id: str) -> dict:
    for item in load_catalog()[section]:
        if item["id"] == item_id:
            return item
    known = [item["id"] for item in load_catalog()[section]]
    raise KeyError(f"Unknown {section[:-1]} id {item_id!r}. Known ids: {known}")


def get_variable(variable_id: str) -> dict:
    """Catalog entry of a variable (name, descriptions, dataset, unit, period, themes)."""
    return _by_id("variables", variable_id)


def get_region(region_id: str) -> dict:
    """Catalog entry of a region (name, name_in_text, bbox, lat/lon, description, themes, compare_with).

    ``name`` is for titles and dropdowns ("Konya Closed Basin"); ``name_in_text``
    reads correctly inside a sentence ("the Konya Closed Basin").
    """
    return _by_id("regions", region_id)


THEMES: dict[str, str] = {t["id"]: t["question"] for t in load_catalog()["themes"]}


def suggest(theme: str) -> list[dict]:
    """Variable x region pairs worth investigating for a theme, best first.

    A pair is suggested when both the variable and the region list the theme.
    Ranking: regions where the theme comes earlier in their ``themes`` list first,
    then the variable order of the theme's ``reasons`` list, then catalog order.
    Each suggestion has a ``reason``: the theme's reason for the variable plus
    the region's one-sentence ``teaser``.
    """
    catalog = load_catalog()
    themes = {t["id"]: t for t in catalog["themes"]}
    if theme not in themes:
        raise KeyError(f"Unknown theme {theme!r}. Known themes: {list(themes)}")

    reasons = [(r["variable_id"], r["reason"]) for r in themes[theme]["reasons"]]
    ranked = []
    for region_index, region in enumerate(catalog["regions"]):
        if theme not in region["themes"]:
            continue
        region_rank = region["themes"].index(theme)
        for var_rank, (variable_id, reason) in enumerate(reasons):
            if theme not in get_variable(variable_id)["themes"]:
                continue
            ranked.append((
                (region_rank, var_rank, region_index),
                {
                    "variable_id": variable_id,
                    "region_id": region["id"],
                    "reason": f"{reason} {region['teaser']}",
                },
            ))
    ranked.sort(key=lambda pair: pair[0])
    return [suggestion for _, suggestion in ranked]


def glossary() -> dict[str, str]:
    """Term -> plain-language definition, in catalog order."""
    return {g["term"]: g["definition"] for g in load_catalog()["glossary"]}


def _matches(rule_value, actual) -> bool:
    return rule_value == WILDCARD or rule_value == actual


def next_step(result: dict, variable_id: str, region_id: str) -> dict:
    """Detective-style next step for an ``analyze_trend`` result.

    Looks up the first rule in ``catalog.json["hints"]`` matching
    (variable, direction, significant); ``"*"`` matches anything. Placeholders
    ``{region}``, ``{compare_region}``, ``{region_id}``, ``{compare_region_id}``
    and ``{variable_id}`` are filled in. Returns the hint text (``text``,
    English; ``text_tr``, Turkish, with the regions' ``name_tr``) plus the
    variable/region the hint points to (``None`` when there is no follow-up),
    so the UI can offer a "follow the clue" button.
    """
    region = get_region(region_id)
    get_variable(variable_id)  # validate the id
    compare = get_region(region["compare_with"])
    values = {
        "region": region["name_in_text"],
        "region_id": region["id"],
        "compare_region": compare["name_in_text"],
        "compare_region_id": compare["id"],
        "variable_id": variable_id,
    }
    direction = result["direction"]
    significant = bool(result["significant"])

    for rule in load_catalog()["hints"]:
        if (_matches(rule["variable_id"], variable_id)
                and _matches(rule["direction"], direction)
                and _matches(rule["significant"], significant)):
            nxt = rule["next"]
            values_tr = {**values, "region": region.get("name_tr", region["name"]),
                         "compare_region": compare.get("name_tr", compare["name"])}
            return {
                "text": rule["text"].format(**values),
                "text_tr": rule.get("text_tr", rule["text"]).format(**values_tr),
                "variable_id": nxt["variable_id"].format(**values) if nxt else None,
                "region_id": nxt["region_id"].format(**values) if nxt else None,
            }
    raise LookupError("catalog.json hints table has no catch-all rule")  # pragma: no cover


def next_step_hint(result: dict, variable_id: str, region_id: str) -> str:
    """Detective-style sentence suggesting what to look at next."""
    return next_step(result, variable_id, region_id)["text"]


CONTEXT_KEYS = ("increasing", "decreasing", "no_clear_trend")


def get_context(result: dict, variable_id: str) -> dict:
    """Real-world context ("What does this mean?") for an ``analyze_trend`` result.

    Picks ``variables[].context["increasing" | "decreasing"]`` only when the trend
    is significant; anything else (not significant, or B's "no change" direction)
    gets ``"no_clear_trend"``, so the UI never attaches a story to noise.
    Returns ``{"key", "text", "text_tr", "sources": [{"title", "url"}, ...]}``
    (``text_tr`` is the Turkish version from ``variables[].context_tr``).
    """
    variable = get_variable(variable_id)
    context = variable["context"]
    key = _trend_key(result) or "no_clear_trend"
    return {"key": key, "text": context[key], "text_tr": variable["context_tr"][key],
            "sources": list(context["sources"])}


def _trend_key(result: dict) -> str | None:
    """"increasing" / "decreasing" for a significant trend, otherwise None."""
    direction = result["direction"]
    if bool(result["significant"]) and direction in ("increasing", "decreasing"):
        return direction
    return None
