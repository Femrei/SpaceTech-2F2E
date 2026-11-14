"""Earth Trend Detective: FastAPI backend (owner: C).

Wraps teammates' Python modules (A: data_loader, B: trend, D: detective) in a
small JSON API for the React frontend in ``frontend/``. Teammates' code is
used unchanged; while a module has not landed yet, a TEMP stub from
``src/stubs`` is used instead.

Dev:   uvicorn api:app --reload            (frontend: cd frontend && npm run dev)
Prod:  cd frontend && npm run build, then  uvicorn api:app
       (the built frontend in frontend/dist is served by this same app)
"""
from __future__ import annotations

import importlib
import math
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent


# Takım arkadaşının modülünü yükler (ör. src.trend).
# Gerçek modül henüz yoksa src/stubs altındaki geçici sürümü kullanır.
# İkinci dönen değer True ise stub kullanılıyor demektir.
def _load_module(name: str):
    try:
        return importlib.import_module(f"src.{name}"), False
    except ModuleNotFoundError as err:
        if err.name != f"src.{name}":  # the real module exists but is broken: surface it
            raise
        return importlib.import_module(f"src.stubs.{name}"), True


data_loader, _stub_a = _load_module("data_loader")   # A
trend, _stub_b = _load_module("trend")               # B
detective, _stub_d = _load_module("detective")       # D
STUBS_IN_USE = [n for n, s in [("data_loader (A)", _stub_a), ("trend (B)", _stub_b),
                                ("detective (D)", _stub_d)] if s]

app = FastAPI(title="Earth Trend Detective API")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
# NaN / sonsuz değerleri JSON'da geçerli olan null'a çevirir (JSON NaN desteklemez).
def _num(x) -> float | None:
    if x is None:
        return None
    x = float(x)
    return None if math.isnan(x) or math.isinf(x) else x


# Tarihleri ondalık yıla çevirir (ör. Temmuz 2010 -> 2010.5).
def _decimal_years(index: pd.DatetimeIndex) -> np.ndarray:
    return (index.year + (index.month - 1) / 12).to_numpy(dtype=float)


# Güven bandını hesaplar: trend çizgisinin orta noktasından geçen, eğimleri
# ci_low ve ci_high olan iki doğru. Orta noktadan uçlara doğru yelpaze gibi açılır.
def _ci_fan(result: dict) -> tuple[pd.Series, pd.Series]:
    trend_line = result["trend_line"].dropna()
    t = _decimal_years(trend_line.index)
    t_mid = (t[0] + t[-1]) / 2
    y_mid = float(np.interp(t_mid, t, trend_line.to_numpy()))
    low = y_mid + result["ci_low"] / 10 * (t - t_mid)
    high = y_mid + result["ci_high"] / 10 * (t - t_mid)
    return (pd.Series(np.minimum(low, high), index=trend_line.index),
            pd.Series(np.maximum(low, high), index=trend_line.index))


# Bir bölge + değişken için seriyi yükler ve B'nin trend analizini çalıştırır.
# Sonuç önbellekte tutulur; aynı istek ikinci kez hesaplanmaz.
@lru_cache(maxsize=64)
def _analyse(region_id: str, variable_id: str) -> tuple[pd.Series, dict]:
    series = data_loader.load_series(region_id, variable_id)
    return series, trend.analyze_trend(series)


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #
# Arayüzün açılışta ihtiyaç duyduğu her şey: katalog (bölgeler, değişkenler,
# sözlük, vakalar), temalar, verisi olan çiftler, veri indirme tarihi, stub listesi.
@app.get("/api/meta")
def meta() -> dict:
    catalog = detective.load_catalog()
    return {
        "variables": catalog["variables"],
        "regions": catalog["regions"],
        "glossary": detective.glossary(),
        "cases": detective.get_cases(),
        "themes": detective.THEMES,
        "pairs": [list(p) for p in data_loader.available_pairs()],
        "data_downloaded_on": data_loader.DATA_DOWNLOADED_ON,
        "stubs_in_use": STUBS_IN_USE,
    }


# Explore sekmesinin verisi: grafik için aylık noktalar (ham değer, 12 aylık
# ortalama, anomali, trend, güven bandı) + sonuç kartı için istatistikler,
# B'nin interpret() metni ve D'nin next_step_hint() önerisi.
@app.get("/api/analysis")
def analysis(region: str, variable: str) -> dict:
    try:
        region_info = detective.get_region(region)
        variable_info = detective.get_variable(variable)
    except KeyError as err:
        raise HTTPException(404, f"Unknown id: {err}") from err
    if (region, variable) not in set(data_loader.available_pairs()):
        raise HTTPException(404, "No data for this region and variable.")
    try:
        series, result = _analyse(region, variable)
    except ValueError as err:  # B raises ValueError when there is not enough data
        raise HTTPException(422, str(err)) from err

    # Full 12-month window only: a partial window at the edges would be biased by
    # the seasonal cycle (e.g. only summer months) and show a fake jump. Interior
    # single missing months are interpolated first so they don't punch 12-month holes.
    smooth = (series.interpolate(limit_area="inside")
              .rolling(12, center=True, min_periods=12).mean())
    low, high = _ci_fan(result)
    points = [
        {
            "date": d.strftime("%Y-%m-%d"),
            "value": _num(series.get(d)),
            "smooth": _num(smooth.get(d)),
            "anomaly": _num(result["anomalies"].get(d)),
            "trend": _num(result["trend_line"].get(d)),
            "ci_low": _num(low.get(d)),
            "ci_high": _num(high.get(d)),
        }
        for d in series.index
    ]
    stats = {}
    for k, v in result.items():  # scalar fields only; Series go into `points`
        if isinstance(v, pd.Series):
            continue
        if isinstance(v, (bool, np.bool_)):
            stats[k] = bool(v)
        elif isinstance(v, (int, np.integer)):
            stats[k] = int(v)
        elif isinstance(v, (float, np.floating)):
            stats[k] = _num(v)
        else:
            stats[k] = v
    return {
        "points": points,
        "result": stats,
        "interpretation": trend.interpret(result, variable_info, region_info),
        "next_step_hint": detective.next_step_hint(result, variable, region),
    }


# Derlenmiş React arayüzü (frontend/dist) varsa onu da bu sunucudan yayınlar;
# böylece canlıya tek bir servis olarak alınabilir.
_DIST = ROOT / "frontend" / "dist"
if _DIST.exists():
    app.mount("/", StaticFiles(directory=_DIST, html=True), name="frontend")
