"""Trend Dedektifi 3B: uygulamanın sunucusu (owner: D).

Bu sunucu üç iş yapar:
1. index.html ve data.js dosyalarını yayınlar.
2. POST /api/chat isteğini karşılar. LLM, repodaki analiz fonksiyonlarını
   araç olarak çağırır ve sonucu açıklar. Bilimsel hesabı LLM değil, B'nin
   trend analizi ve D'nin kataloğu yapar.
3. GET /api/point ve /api/box: "Alan seç" modunda kullanıcının seçtiği nokta
   ya da kutu için C'nin api.py fonksiyonlarını çağırır (NASA POWER, canlı).

Repodaki diğer dosyalar yalnızca okunur, hiçbiri değiştirilmez.

Çalıştırma (repo kökünden):
    python detective3d/agent_server.py
Ardından http://localhost:8765 adresini aç.
HOST ve PORT ortam değişkenleri adresi değiştirir (Docker: HOST=0.0.0.0).

LLM: .env dosyasında LLM_PROVIDER (groq, gemini, openrouter, ollama, anthropic) ve anahtarı.
Yoksa sohbet "çevrimdışı moda" düşer. Bu modda LLM yoktur; anahtar kelimelerle
bölge ve değişkeni bulup D'nin ipucu zincirini gösterir.
"""
from __future__ import annotations

import json
import os
import re
import sys
import uuid
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = Path(os.environ.get("TREND_REPO", HERE.parent)).resolve()  # repo root (this folder's parent)
sys.path.insert(0, str(REPO))
_cwd = os.getcwd()
os.chdir(REPO)  # api.py / data_loader read paths relative to the repo
import api  # noqa: E402  (C's FastAPI module; we only call its functions)
from src import detective, trend  # noqa: E402
os.chdir(_cwd)

import anthropic  # noqa: E402
from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.responses import FileResponse  # noqa: E402
from pydantic import BaseModel  # noqa: E402

def _load_dotenv(path: Path) -> None:
    """Read KEY=VALUE lines from .env (no extra dependency). Real env vars win."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip('"').strip("'")
        if value:
            os.environ.setdefault(key.strip(), value)


_load_dotenv(HERE / ".env")

# --------------------------------------------------------------------------- #
# LLM provider (set in .env)
#   LLM_PROVIDER = groq | gemini | openrouter | ollama | anthropic   (empty → offline mode)
#   LLM_API_KEY  = key of that provider (not needed for ollama; anthropic uses ANTHROPIC_API_KEY)
#   LLM_MODEL    = optional model override
# The free providers all speak the OpenAI-compatible Chat Completions API.
# --------------------------------------------------------------------------- #
FREE_PROVIDERS = {
    "groq": {"label": "Groq", "base_url": "https://api.groq.com/openai/v1",
             "model": "openai/gpt-oss-120b"},
    "gemini": {"label": "Google Gemini", "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
               "model": "gemini-flash-latest"},
    "openrouter": {"label": "OpenRouter", "base_url": "https://openrouter.ai/api/v1",
                   "model": "meta-llama/llama-3.3-70b-instruct:free"},
    "ollama": {"label": "Ollama (yerel)", "base_url": "http://localhost:11434/v1", "model": "qwen2.5:7b"},
}
PROVIDER = os.environ.get("LLM_PROVIDER", "").strip().lower() or (
    "anthropic" if os.environ.get("ANTHROPIC_API_KEY") else "")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")

# Claude (paid) settings, used only when LLM_PROVIDER=anthropic.
CLAUDE_MODEL = os.environ.get("AGENT_MODEL") or "claude-opus-5-5"
# Server-side refusal fallback exists for these models only (not for Haiku).
FALLBACK_MODELS = {"claude-opus-5-5", "claude-sonnet-5-5", "claude-fable-5-2", "claude-fable-5-1", "claude-opus-5"}

if PROVIDER in FREE_PROVIDERS:
    MODEL = os.environ.get("LLM_MODEL") or FREE_PROVIDERS[PROVIDER]["model"]
    PROVIDER_LABEL = FREE_PROVIDERS[PROVIDER]["label"]
elif PROVIDER == "anthropic":
    MODEL, PROVIDER_LABEL = CLAUDE_MODEL, "Claude"
else:
    MODEL, PROVIDER_LABEL = None, None
MAX_TOOL_ROUNDS = 8

REGIONS = {r["id"]: r for r in detective.load_catalog()["regions"]}
VARIABLES = {v["id"]: v for v in detective.load_catalog()["variables"]}
REGION_IDS = sorted(REGIONS)
VARIABLE_IDS = sorted(VARIABLES)
YEARS = (2001, 2025)


def _load_js(path: Path) -> dict:
    """Read a 'window.X = {...};' data file produced by build_data.py / build_power.py."""
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    return json.loads(text[text.index("=") + 1:].strip().rstrip(";"))


SOURCES = {k: v.get("source") for k, v in _load_js(HERE / "data.js").get("pairs", {}).items()}
POWER = _load_js(HERE / "power_data.js")
NDVI = _load_js(HERE / "ndvi_data.js")
POWER_PARAMS = {"temp": ["T2M", "T2M_MAX"], "precip": ["PRECTOTCORR"], "soil_moisture": ["GWETROOT"]}


# --------------------------------------------------------------------------- #
# Tools: thin wrappers over the repo's analysis (B) and catalog (D)
# --------------------------------------------------------------------------- #
def _round(x, n=4):
    return None if x is None else round(float(x), n)


def tool_get_trend(region: str, variable: str) -> dict:
    a = api.analysis(region, variable)
    r = a["result"]
    _, result = api._analyse(region, variable)
    return {
        "region": REGIONS[region]["name"],
        "variable": VARIABLES[variable]["name"],
        "unit": VARIABLES[variable]["unit"],
        "period": f'{r.get("start_year")}–{r.get("end_year")}',
        "sen_slope_per_decade": _round(r["sen_slope_per_decade"]),
        "ci95_per_decade": [_round(r["ci_low"]), _round(r["ci_high"])],
        "percent_change_per_decade": None if variable in getattr(trend, "NO_PERCENT_VARIABLES", ())
        else _round(r["percent_change_per_decade"], 2),
        "mann_kendall_p": r["mk_p"],
        "significant_at_0_05": r["significant"],
        "direction": r["direction"],
        "long_term_mean": _round(r["mean_value"]),
        "interpretation": a["interpretation"],
        "detective_next_step": a["next_step"],
        "what_it_means": detective.get_context(result, variable),
        "source": SOURCES.get(f"{region}|{variable}"),
    }


def tool_get_ndvi_trend(region: str) -> dict:
    if not NDVI:
        raise ValueError("ndvi_data.js is missing; run build_ndvi.py first.")
    if region not in NDVI["sites"]:
        raise ValueError(f"MODIS NDVI for {REGIONS[region]['name']} has not been downloaded yet "
                         "(the ORNL server was overloaded). Say that NDVI is not available for this region yet.")
    site, ser = NDVI["sites"][region], NDVI["series"][region]
    return {
        "region": REGIONS[region]["name"],
        "site": {"name": site["name"], "kind": site["kind"], "lat": site["lat"], "lon": site["lon"],
                 "window_km": NDVI["window_km"], "land_cover_2020": site["land_cover"]},
        "monthly_trend_2001_2025": ser["trend"],
        "peak_greenness_trend": {k: ser["peak"][k] for k in ("sen_slope_per_decade", "mk_p", "significant", "direction")},
        "peak_by_year": dict(zip(ser["peak"]["years"], ser["peak"]["values"])),
        "caveats": [
            "NDVI is measured in one 10 km x 10 km window chosen with MODIS land cover, not over the whole region box.",
            "Monthly value = maximum of the 16-day composites in that month (reduces cloud effects).",
            "Greening on irrigated cropland can come from more irrigation or crop changes, not from more rain; "
            "browning can come from fallow, crop rotation or drought. NDVI alone cannot tell which.",
        ],
        "source": NDVI["source"],
    }


def tool_get_long_record(region: str, variable: str) -> dict:
    if not POWER:
        raise ValueError("power_data.js is missing; run build_power.py first.")
    out = {
        "region": REGIONS[region]["name"],
        "dataset": "NASA POWER monthly (MERRA-2 based meteorology; PRECTOTCORR bias-corrected precipitation; "
                   "GWETROOT = root-zone soil wetness 0-100 %)",
        "comparability_note": (
            "Different product from the main analysis (Giovanni: IMERG precipitation, GLDAS 0-10 cm soil "
            "moisture in kg/m², MERRA-2 T2M). Area mean of the POWER grid-cell centres inside the same box. "
            "Root-zone wetness is not the same quantity as surface soil moisture."),
        "grid_points": len(POWER["points"].get(region, [])),
        "series": [],
        "source": {"dataset": "NASA POWER monthly point API (community=AG), 1981-2025",
                   "url": POWER["source"]["url"], "via": "NASA POWER"},
    }
    for param in POWER_PARAMS[variable]:
        item = POWER["series"][f"{region}|{param}"]
        out["series"].append({
            "parameter": param, "label": POWER["variables"][param]["label"],
            "unit_per_decade": POWER["variables"][param]["unit"],
            "trend_1981_2025": item["full"], "trend_2001_2025": item["recent"],
        })
    return out


def tool_compare_regions(variable: str, region_a: str, region_b: str) -> dict:
    c = api.compare(variable, region_a, region_b)
    pick = lambda r: {k: r.get(k) for k in ("sen_slope_per_decade", "significant", "direction", "mk_p")}
    return {
        "variable": VARIABLES[variable]["name"],
        "unit": VARIABLES[variable]["unit"],
        "region_a": REGIONS[region_a]["name"], "result_a": pick(c["result_a"]),
        "region_b": REGIONS[region_b]["name"], "result_b": pick(c["result_b"]),
        "comparison": c["comparison"],
    }


def tool_get_overview() -> list[dict]:
    return [
        {k: item.get(k) for k in ("region_id", "variable_id", "sen_slope_per_decade",
                                  "significant", "direction", "mk_p", "error")}
        for item in api.overview()
    ]


def tool_get_period_stats(region: str, variable: str, start_year: int, end_year: int) -> dict:
    series, result = api._analyse(region, variable)
    s = series[(series.index.year >= start_year) & (series.index.year <= end_year)].dropna()
    if s.empty:
        raise ValueError(f"No data between {start_year} and {end_year}.")
    yearly = s.groupby(s.index.year).agg(["mean", "count"])
    return {
        "region": REGIONS[region]["name"], "variable": VARIABLES[variable]["name"],
        "unit": VARIABLES[variable]["unit"],
        "period_mean": _round(s.mean()), "long_term_mean": _round(result["mean_value"]),
        "difference_from_long_term_mean": _round(s.mean() - result["mean_value"]),
        "months_with_data": int(s.size),
        "yearly_means": {int(y): _round(m) for y, (m, n) in yearly.iterrows()},
        "min_month": {"date": s.idxmin().strftime("%Y-%m"), "value": _round(s.min())},
        "max_month": {"date": s.idxmax().strftime("%Y-%m"), "value": _round(s.max())},
    }


def tool_get_background(region: str | None = None, variable: str | None = None) -> dict:
    out: dict = {}
    if region:
        r = REGIONS[region]
        out["region"] = {k: r.get(k) for k in ("name", "description", "bbox", "themes")}
    if variable:
        v = VARIABLES[variable]
        out["variable"] = {k: v.get(k) for k in ("name", "long_description", "dataset", "source",
                                                 "resolution", "unit", "period", "period_note")}
    if not out:
        out["glossary"] = detective.glossary()
    return out


# control_map is not executed here: its actions are sent to the browser.
TOOLS = [
    {
        "name": "get_trend",
        "description": (
            "Run the team's trend analysis (seasonal Mann-Kendall test + Sen slope on monthly NASA "
            "Giovanni area averages, 2001-2025) for one region and variable. Returns the slope per "
            "decade, 95% CI, p-value, significance, the team's plain-language interpretation, the "
            "catalog's detective next-step hint and real-world context. Use this for any question "
            "about whether something is changing."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "region": {"type": "string", "enum": REGION_IDS},
                "variable": {"type": "string", "enum": VARIABLE_IDS},
            },
            "required": ["region", "variable"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "name": "compare_regions",
        "description": "Compare the trend of one variable between two regions (direction and significance).",
        "input_schema": {
            "type": "object",
            "properties": {
                "variable": {"type": "string", "enum": VARIABLE_IDS},
                "region_a": {"type": "string", "enum": REGION_IDS},
                "region_b": {"type": "string", "enum": REGION_IDS},
            },
            "required": ["variable", "region_a", "region_b"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "name": "get_overview",
        "description": "Trend summary for every region × variable pair at once. Use for broad questions.",
        "input_schema": {"type": "object", "properties": {}, "required": [], "additionalProperties": False},
        "strict": True,
    },
    {
        "name": "get_period_stats",
        "description": (
            "Mean, yearly means and extreme months of one series between two years (inclusive), "
            "compared with the 2001-2025 long-term mean. Use for questions about specific years or "
            "periods (e.g. a drought year, before vs. after)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "region": {"type": "string", "enum": REGION_IDS},
                "variable": {"type": "string", "enum": VARIABLE_IDS},
                "start_year": {"type": "integer"},
                "end_year": {"type": "integer"},
            },
            "required": ["region", "variable", "start_year", "end_year"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "name": "get_long_record",
        "description": (
            "Long-record check with a second, independent NASA dataset: NASA POWER 1981-2025 for the same "
            "region box. Returns seasonal Mann-Kendall + Sen results for 1981-2025 and for 2001-2025 "
            "(temp -> T2M and daily-max T2M_MAX; precip -> bias-corrected PRECTOTCORR; soil_moisture -> "
            "root-zone soil wetness GWETROOT). Use it to ask 'is this a long-term trend or only since 2001?' "
            "and to cross-check the main result. If the datasets disagree, say so."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "region": {"type": "string", "enum": REGION_IDS},
                "variable": {"type": "string", "enum": VARIABLE_IDS},
            },
            "required": ["region", "variable"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "name": "get_ndvi_trend",
        "description": (
            "Vegetation greenness trend from MODIS Terra NDVI (MOD13Q1, 250 m), 2001-2025, in a 10 km x 10 km "
            "farm window inside the region (konya: Çumra plain, van: Erciş plain; black_sea has no cropland in "
            "MODIS land cover, so its window is natural vegetation on the Rize coastal slopes). Returns the "
            "seasonal Mann-Kendall + Sen trend of monthly NDVI, the trend of each year's peak NDVI, land cover "
            "shares and caveats. Use it for questions about crops, vegetation or farming."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"region": {"type": "string", "enum": REGION_IDS}},
            "required": ["region"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "name": "get_background",
        "description": (
            "Catalog background: a region's description and bounding box, a variable's dataset, "
            "resolution and period. With no arguments, returns the glossary of statistical terms."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "region": {"type": "string", "enum": REGION_IDS},
                "variable": {"type": "string", "enum": VARIABLE_IDS},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "control_map",
        "description": (
            "Drive the 3D map the user is looking at so it shows what you are talking about. "
            "Every field is optional (omit = leave unchanged): fly to a region (or 'overview' for "
            "all of Türkiye), switch the variable, jump to a month (YYYY-MM, 2001-01..2025-12), "
            "switch the view mode ('time' = monthly animation, 'before' = 2001-05 mean, 'after' = "
            "2021-25 mean), or toggle the NDVI imagery layer. Call it once per answer when a view "
            "helps, usually before you write the answer."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "region": {"type": "string", "enum": [*REGION_IDS, "overview"]},
                "variable": {"type": "string", "enum": VARIABLE_IDS},
                "month": {"type": "string", "pattern": "^20[0-2][0-9]-(0[1-9]|1[0-2])$"},
                "mode": {"type": "string", "enum": ["time", "before", "after"]},
                "ndvi": {"type": "boolean"},
            },
            "additionalProperties": False,
        },
    },
]

HANDLERS = {
    "get_trend": tool_get_trend,
    "compare_regions": tool_compare_regions,
    "get_overview": lambda: tool_get_overview(),
    "get_period_stats": tool_get_period_stats,
    "get_background": tool_get_background,
    "get_long_record": tool_get_long_record,
    "get_ndvi_trend": tool_get_ndvi_trend,
}

STEP_LABELS = {
    "get_trend": "Trend analizi",
    "compare_regions": "Bölge karşılaştırması",
    "get_overview": "Genel tarama",
    "get_period_stats": "Dönem istatistiği",
    "get_background": "Katalog bilgisi",
    "get_long_record": "45 yıllık kontrol (POWER)",
    "get_ndvi_trend": "Bitki örtüsü (MODIS NDVI)",
    "control_map": "Harita",
}
TR_REGION = {"konya": "Konya", "van": "Van", "black_sea": "Doğu Karadeniz", "overview": "Türkiye"}
TR_VAR = {"precip": "yağış", "soil_moisture": "toprak nemi", "temp": "sıcaklık"}


def _step_label(name: str, args: dict) -> str:
    bits = [TR_REGION.get(args.get(k), args.get(k)) for k in ("region", "region_a", "region_b") if args.get(k)]
    if args.get("variable"):
        bits.append(TR_VAR.get(args["variable"], args["variable"]))
    if args.get("start_year"):
        bits.append(f'{args["start_year"]}–{args["end_year"]}')
    for k in ("month", "mode"):
        if args.get(k):
            bits.append(str(args[k]))
    return STEP_LABELS.get(name, name) + (": " + " · ".join(bits) if bits else "")


SYSTEM = """You are the Trend Detective assistant inside a 3D map of Türkiye built for the NASA Space Apps \
challenge "Be an Earth System Trend Detective". You think like a team of an agronomist, a hydrologist and a \
climate scientist, and you talk to farmers, students and judges.

Data you can reach through tools (and nothing else):
- Three regions: konya (Konya Closed Basin, semi-arid grain basin, groundwater-irrigated), van (Lake Van \
Basin, high plateau) and black_sea (Eastern Black Sea, mostly mountains in our box).
- Three monthly variables, 2001-2025, from NASA Giovanni as area averages over each region's box (~25 km grid): \
precip (mm/month), soil_moisture (surface 0-10 cm, kg/m²), temp (2 m air temperature, °C).
- The team's statistics: seasonal Mann-Kendall test + Sen slope, significance at p < 0.05.

How to work:
- Get every number from a tool. Never estimate or recall values. If the tools can't answer, say so.
- Follow the clue chain like a detective: when a series changes, check the variables that could explain it \
(e.g. drying soil -> was it less rain or more heat?), using the catalog's next-step hint.
- Use get_long_record to check whether a trend is long-term (1981-2025) or only recent (2001-2025), and to
cross-check with an independent dataset. When the two datasets disagree, say so plainly, give the likely
reasons (different products and depths, coarse grids, mountains) and suggest checking local station data
(MGM) instead of picking a winner.
- Use get_ndvi_trend for crops and vegetation. Combine it with water clues carefully: e.g. greener
irrigated fields while the soil dries may point to more groundwater irrigation, but say this is a
hypothesis, not a finding.
- Use control_map so the map shows what you are describing.
- Be honest about limits: these are regional averages, not field measurements; a trend is not a cause; \
"not significant" means it can't yet be told apart from natural variability, not "no change". For farm \
advice (irrigation, crops, fertiliser) explain what the data suggests and what local measurement \
(soil test, field sensors) would be needed; never prescribe doses.
- Answer in the user's language (usually Turkish). Keep it short: 3-6 sentences or a few bullets, with the \
key numbers and units. Plain words first, statistics second. End with one suggested next question when useful.
- Finish with a short line "Kaynak:" naming the datasets you used (the source fields in tool results)."""


# --------------------------------------------------------------------------- #
# Agent loop
# --------------------------------------------------------------------------- #
SESSIONS: dict[str, list] = {}
_client: anthropic.Anthropic | None = None
_oai_client = None


def _has_credentials() -> bool:
    """True when an LLM is configured (otherwise the chat runs in offline mode)."""
    if PROVIDER == "anthropic":
        return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))
    if PROVIDER == "ollama":
        return True
    return PROVIDER in FREE_PROVIDERS and bool(LLM_API_KEY)


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def _map_note(ui_state: dict) -> str:
    return (f"[Map state: region={ui_state.get('region')}, variable={ui_state.get('variable')}, "
            f"month={ui_state.get('month')}, mode={ui_state.get('mode')}]")


def _add_source(sources: list, src) -> None:
    if src and src.get("dataset") and src not in sources:
        sources.append(src)


def _run_tool(name: str, args: dict, steps: list, actions: list, sources: list) -> str:
    """Execute one tool call; control_map is queued for the browser instead."""
    steps.append(_step_label(name, args))
    if name == "control_map":
        actions.append({k: v for k, v in args.items() if v is not None})
        return "Map updated."
    if name not in HANDLERS:
        raise ValueError(f"Unknown tool: {name}")
    result = HANDLERS[name](**args)
    if isinstance(result, dict):
        _add_source(sources, result.get("source"))
    if name == "compare_regions":
        for key in ("region_a", "region_b"):
            _add_source(sources, SOURCES.get(f"{args[key]}|{args['variable']}"))
    return json.dumps(result, ensure_ascii=False, default=str)


# ---- free providers (OpenAI-compatible Chat Completions) -------------------- #
def _oai_schema(schema):
    """Drop JSON-schema keywords some providers (e.g. Gemini) reject."""
    if isinstance(schema, dict):
        return {k: _oai_schema(v) for k, v in schema.items()
                if k not in ("additionalProperties", "pattern") and not (k == "required" and not v)}
    if isinstance(schema, list):
        return [_oai_schema(x) for x in schema]
    return schema


OAI_TOOLS = [{"type": "function", "function": {"name": t["name"], "description": t["description"],
                                               "parameters": _oai_schema(t["input_schema"])}} for t in TOOLS]
# Provider-specific extras that must not be sent back in the history.
_DROP_FIELDS = ("reasoning", "reasoning_content", "reasoning_details", "refusal", "annotations",
                "audio", "function_call", "executed_tools", "channel")


def _get_oai_client():
    global _oai_client
    if _oai_client is None:
        import openai
        # LLM_BASE_URL: any other OpenAI-compatible endpoint (LM Studio, a test mock, ...)
        base_url = os.environ.get("LLM_BASE_URL") or FREE_PROVIDERS[PROVIDER]["base_url"]
        _oai_client = openai.OpenAI(base_url=base_url,
                                    api_key=LLM_API_KEY or "ollama", max_retries=2, timeout=120)
    return _oai_client


def _trim_history(messages: list, keep_turns: int = 4) -> None:
    """Keep the system message and the last few user turns (free tiers have small token limits)."""
    user_idx = [i for i, m in enumerate(messages) if m.get("role") == "user"]
    if len(user_idx) > keep_turns:
        del messages[1:user_idx[-keep_turns]]


def run_agent_free(session_id: str, user_text: str, ui_state: dict) -> dict:
    client = _get_oai_client()
    messages = SESSIONS.setdefault(session_id, [{"role": "system", "content": SYSTEM}])
    _trim_history(messages)
    messages.append({"role": "user", "content": f"{_map_note(ui_state)}\n{user_text}"})
    steps, actions, sources = [], [], []

    for _ in range(MAX_TOOL_ROUNDS):
        response = client.chat.completions.create(
            model=MODEL, messages=messages, tools=OAI_TOOLS, tool_choice="auto",
            temperature=0.2, max_tokens=4096,
        )
        choice = response.choices[0]
        msg = choice.message
        entry = msg.model_dump(exclude_none=True)  # keeps provider extras such as Gemini thought signatures
        for k in _DROP_FIELDS:
            entry.pop(k, None)
        entry["content"] = entry.get("content") or ""
        messages.append(entry)

        if not msg.tool_calls:
            text = (msg.content or "").strip()
            if choice.finish_reason == "length":
                text += "\n\n(Yanıt uzunluk sınırında kesildi.)"
            return {"text": text or "(boş yanıt)", "steps": steps, "actions": actions, "sources": sources}

        for call in msg.tool_calls:
            try:
                args = json.loads(call.function.arguments or "{}") or {}
                content = _run_tool(call.function.name, args, steps, actions, sources)
            except Exception as err:  # report to the model, don't crash the turn
                content = f"Error: {err}"
            messages.append({"role": "tool", "tool_call_id": call.id, "content": content})

    return {"text": "Çok fazla adım gerekti; soruyu daha dar sorabilir misin?", "steps": steps, "actions": actions, "sources": sources}


# ---- Claude (paid) ---------------------------------------------------------- #
def run_agent(session_id: str, user_text: str, ui_state: dict) -> dict:
    messages = SESSIONS.setdefault(session_id, [])
    messages.append({"role": "user", "content": f"{_map_note(ui_state)}\n{user_text}"})
    steps, actions, sources = [], [], []

    for _ in range(MAX_TOOL_ROUNDS):
        extra = ({"betas": ["server-side-fallback-2026-07-01"], "fallbacks": "default"}
                 if MODEL in FALLBACK_MODELS else {})
        response = _get_client().beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            system=SYSTEM,
            tools=TOOLS,
            messages=messages,
            output_config={"effort": "medium"},
            **extra,
        )
        # Keep the full content (thinking + tool_use blocks) so the next turn replays it unchanged.
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "refusal":
            return {"text": "Bu isteğe yanıt veremiyorum. Soruyu verilerle ilgili olacak şekilde yeniden sorabilirsin.",
                    "steps": steps, "actions": actions, "sources": sources}
        if response.stop_reason == "pause_turn":
            continue
        if response.stop_reason != "tool_use":
            text = "\n".join(b.text for b in response.content if b.type == "text").strip()
            if response.stop_reason == "max_tokens":
                text += "\n\n(Yanıt uzunluk sınırında kesildi.)"
            return {"text": text, "steps": steps, "actions": actions, "sources": sources}

        results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            try:
                content = _run_tool(block.name, dict(block.input or {}), steps, actions, sources)
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": content})
            except Exception as err:  # report to the model, don't crash the turn
                results.append({"type": "tool_result", "tool_use_id": block.id,
                                "content": f"Error: {err}", "is_error": True})
        messages.append({"role": "user", "content": results})

    return {"text": "Çok fazla adım gerekti; soruyu daha dar sorabilir misin?", "steps": steps, "actions": actions, "sources": sources}


# --------------------------------------------------------------------------- #
# Offline mode: no LLM, keyword routing + D's clue chain
# --------------------------------------------------------------------------- #
KEYWORDS = {
    "region": {"konya": ["konya"], "van": ["van"], "black_sea": ["karadeniz", "black sea", "rize", "trabzon"]},
    "variable": {"precip": ["yağış", "yagis", "yağmur", "yagmur", "rain", "precip"],
                 "soil_moisture": ["toprak", "nem", "kuraklık", "kurak", "soil", "drought"],
                 "temp": ["sıcak", "sicak", "ısın", "isin", "temp", "warm", "heat"]},
}


def _find(kind: str, text: str) -> list[str]:
    t = text.lower()
    return [k for k, words in KEYWORDS[kind].items() if any(w in t for w in words)]


def run_offline(user_text: str, ui_state: dict) -> dict:
    regions = _find("region", user_text) or [ui_state.get("region") or "konya"]
    variable = (_find("variable", user_text) or [ui_state.get("variable") or "soil_moisture"])[0]
    steps, actions, lines, sources = [], [], [], []
    for region in regions[:2]:
        t = tool_get_trend(region, variable)
        _add_source(sources, t.get("source"))
        steps.append(_step_label("get_trend", {"region": region, "variable": variable}))
        sig = "anlamlı (p < 0,05)" if t["significant_at_0_05"] else "anlamlı değil"
        yon = {"increasing": "artıyor", "decreasing": "azalıyor"}.get(t["direction"], "belirgin değişmiyor")
        lines.append(f"**{TR_REGION[region]} · {TR_VAR[variable]}**: on yılda {t['sen_slope_per_decade']:+.2f} "
                     f"{t['unit']} ({yon}), eğilim {sig}.")
        hint = t["detective_next_step"]
        if hint.get("text"):
            lines.append(f"İpucu (katalog, İngilizce): {hint['text']}")
        if POWER:
            lr = tool_get_long_record(region, variable)
            steps.append(_step_label("get_long_record", {"region": region, "variable": variable}))
            _add_source(sources, lr["source"])
            for item in lr["series"][:1]:
                f, r = item["trend_1981_2025"], item["trend_2001_2025"]
                mark = lambda x: "anlamlı" if x["significant"] else "anlamlı değil"
                lines.append(f"45 yıllık kontrol ({item['parameter']}, NASA POWER): 1981–2025 "
                             f"{f['sen_slope_per_decade']:+.2f} ({mark(f)}), 2001–2025 "
                             f"{r['sen_slope_per_decade']:+.2f} ({mark(r)}) {item['unit_per_decade']}/10 yıl.")
    if NDVI and any(w in user_text.lower() for w in ("bitki", "ndvi", "tarım", "tarim", "yeşil", "yesil", "ürün", "urun", "tarla")):
        for region in regions[:2]:
            steps.append(_step_label("get_ndvi_trend", {"region": region}))
            try:
                n = tool_get_ndvi_trend(region)
            except ValueError:
                lines.append(f"**{TR_REGION[region]} · NDVI**: veri henüz indirilmedi.")
                continue
            _add_source(sources, n["source"])
            t, pk = n["monthly_trend_2001_2025"], n["peak_greenness_trend"]
            mark = lambda x: "anlamlı" if x["significant"] else "anlamlı değil"
            lines.append(f"**{TR_REGION[region]} · bitki örtüsü (MODIS NDVI, {n['site']['name']})**: aylık "
                         f"{t['sen_slope_per_decade']:+.3f}/10 yıl ({mark(t)}), yıllık zirve "
                         f"{pk['sen_slope_per_decade']:+.3f}/10 yıl ({mark(pk)}).")
    actions.append({"region": regions[0] if len(regions) == 1 else "overview", "variable": variable})
    steps.append(_step_label("control_map", actions[0]))
    lines.append("\n_Çevrimdışı mod: LLM bağlı değil, cevap kural tabanlı. Tam ajan için .env dosyasında "
                 "ücretsiz bir sağlayıcı (LLM_PROVIDER + LLM_API_KEY) tanımla._")
    return {"text": "\n".join(lines), "steps": steps, "actions": actions, "sources": sources, "offline": True}


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #
app = FastAPI(title="Trend Dedektifi 3B")


class ChatIn(BaseModel):
    message: str
    session_id: str | None = None
    ui_state: dict = {}


@app.get("/api/agent-status")
def agent_status() -> dict:
    on = _has_credentials()
    return {"llm": on, "provider": PROVIDER_LABEL if on else None, "model": MODEL if on else None}


# C: "Alan seç" modu (haritada nokta). Seçilen noktanın NASA POWER hücresini
# C'nin api.py'deki point() fonksiyonu ile aynen analiz eder. Hata kodları
# (422 denizde toprak ıslaklığı, 502 POWER'a ulaşılamadı) oradan gelir.
@app.get("/api/point")
def area_point(lat: float, lon: float, variable: str) -> dict:
    return api.point(lat, lon, variable)


# C: "Alan seç" modu (haritada kutu). Çizilen kutunun içindeki NASA POWER
# hücrelerinin alan ağırlıklı ortalamasını api.py'deki box() ile analiz eder.
# Kutunun kenarları en fazla 10 derece olabilir (POWER kuralı).
@app.get("/api/box")
def area_box(south: float, west: float, north: float, east: float, variable: str) -> dict:
    return api.box(south, west, north, east, variable)


def _free_provider_error(err) -> HTTPException:
    """Turn OpenAI-SDK errors from free providers into short Turkish messages."""
    import openai
    if isinstance(err, openai.AuthenticationError):
        return HTTPException(401, f"{PROVIDER_LABEL} anahtarı geçersiz (LLM_API_KEY).")
    if isinstance(err, openai.RateLimitError):
        return HTTPException(429, f"{PROVIDER_LABEL} ücretsiz kotası doldu; bir dakika bekleyip tekrar dene.")
    if isinstance(err, openai.APIConnectionError):
        hint = " Ollama açık mı? (ollama serve)" if PROVIDER == "ollama" else ""
        return HTTPException(503, f"{PROVIDER_LABEL} sunucusuna bağlanılamadı.{hint}")
    if isinstance(err, (openai.NotFoundError, openai.BadRequestError)) and "model" in str(err).lower():
        try:
            names = sorted(m.id for m in _get_oai_client().models.list())[:25]
            listing = " Kullanılabilir modeller: " + ", ".join(names)
        except Exception:
            listing = ""
        return HTTPException(502, f"Model '{MODEL}' bulunamadı veya araç çağırmayı desteklemiyor; "
                                  f".env'de LLM_MODEL ile değiştir.{listing}")
    if isinstance(err, openai.APIStatusError):
        return HTTPException(502, f"{PROVIDER_LABEL} hatası: {err.message}")
    return HTTPException(500, f"Beklenmeyen hata: {err}")


@app.post("/api/chat")
def chat(body: ChatIn) -> dict:
    text = body.message.strip()
    if not text:
        raise HTTPException(400, "Boş mesaj.")
    session_id = body.session_id or uuid.uuid4().hex
    if not _has_credentials():
        return {"session_id": session_id, **run_offline(text, body.ui_state)}
    if PROVIDER in FREE_PROVIDERS:
        import openai
        try:
            out = run_agent_free(session_id, text, body.ui_state)
        except openai.OpenAIError as err:
            SESSIONS.pop(session_id, None)  # a broken history would fail again
            raise _free_provider_error(err)
        return {"session_id": session_id, **out}
    try:
        out = run_agent(session_id, text, body.ui_state)
    except anthropic.AuthenticationError:
        raise HTTPException(401, "API anahtarı geçersiz.")
    except anthropic.RateLimitError:
        raise HTTPException(429, "Hız sınırına takıldı, biraz sonra tekrar dene.")
    except anthropic.APIConnectionError:
        raise HTTPException(503, "Claude API'ye bağlanılamadı (internet?).")
    except anthropic.APIStatusError as err:
        SESSIONS.pop(session_id, None)  # a broken history would fail again
        raise HTTPException(502, f"Claude API hatası: {err.message}")
    return {"session_id": session_id, **out}


@app.post("/api/reset")
def reset(body: ChatIn) -> dict:
    SESSIONS.pop(body.session_id or "", None)
    return {"ok": True}


@app.get("/")
def index():
    return FileResponse(HERE / "index.html")


@app.get("/{name}")
def static_file(name: str):
    if name not in {"index.html", "data.js", "power_data.js", "ndvi_data.js", "cities.js"}:
        raise HTTPException(404)
    return FileResponse(HERE / name)


if __name__ == "__main__":
    import uvicorn

    # Windows'ta çıktı bir dosyaya ya da başka bir programa yönlendirilince Python
    # sistem kodlamasını (Türkçe Windows'ta cp1254) kullanır; "→" gibi karakterler
    # orada yoktur ve print sunucuyu açılışta çökertir. Çıktıyı her zaman UTF-8 yap.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    print("LLM:", f"açık ({PROVIDER_LABEL} · {MODEL})" if _has_credentials() else "kapalı → çevrimdışı mod")
    uvicorn.run(app, host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", 8765)))
