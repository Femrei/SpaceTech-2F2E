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


# 12 aylık hareketli ortalama. Sadece tam 12 aylık pencere kullanılır: kenarlarda
# yarım pencere mevsim etkisiyle sahte bir sıçrama gösterirdi. Serinin içindeki tek
# tük boş aylar önce komşularından doldurulur ki ortalamada 12 aylık delik açmasın.
def _smooth12(series: pd.Series) -> pd.Series:
    return (series.interpolate(limit_area="inside")
            .rolling(12, center=True, min_periods=12).mean())


# Trend sonucundaki tek değerli alanları (Series olmayanları) JSON'a uygun tiplere çevirir.
def _scalars(result: dict) -> dict:
    stats = {}
    for k, v in result.items():  # Series go into the chart points instead
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
    return stats


# Bölge + değişkeni katalogda doğrular, analizi çalıştırır; sorun varsa uygun
# HTTP hatasını fırlatır (404: bilinmeyen id / veri yok, 422: yetersiz veri).
def _checked(region: str, variable: str) -> tuple[dict, dict, pd.Series, dict]:
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
    return region_info, variable_info, series, result


# Pano sekmesinin verisi: grafik için aylık noktalar (ham değer, 12 aylık
# ortalama, anomali, trend, güven bandı) + sonuç kartı için istatistikler,
# B'nin interpret() metni ve D'nin next_step_hint() önerisi.
@app.get("/api/analysis")
def analysis(region: str, variable: str) -> dict:
    region_info, variable_info, series, result = _checked(region, variable)
    smooth = _smooth12(series)
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
    return {
        "points": points,
        "result": _scalars(result),
        "interpretation": trend.interpret(result, variable_info, region_info),
        "next_step_hint": detective.next_step_hint(result, variable, region),
    }


# Karşılaştır sekmesinin verisi: aynı değişken için iki bölgenin anomalileri
# (12 aylık ortalaması alınmış, okunaklı olsun diye) ve trend çizgileri,
# iki bölgenin istatistikleri ve B'nin compare_trends() özeti.
@app.get("/api/compare")
def compare(variable: str, region_a: str, region_b: str) -> dict:
    info_a, variable_info, _, res_a = _checked(region_a, variable)
    info_b, _, _, res_b = _checked(region_b, variable)
    smooth_a, smooth_b = _smooth12(res_a["anomalies"]), _smooth12(res_b["anomalies"])
    index = res_a["anomalies"].index.union(res_b["anomalies"].index)
    points = [
        {
            "date": d.strftime("%Y-%m-%d"),
            "a": _num(smooth_a.get(d)),
            "b": _num(smooth_b.get(d)),
            "trend_a": _num(res_a["trend_line"].get(d)),
            "trend_b": _num(res_b["trend_line"].get(d)),
        }
        for d in index
    ]
    summary = trend.compare_trends(res_a, res_b, info_a, info_b)
    return {
        "points": points,
        "result_a": _scalars(res_a),
        "result_b": _scalars(res_b),
        "comparison": {k: (bool(v) if isinstance(v, (bool, np.bool_)) else v)
                       for k, v in summary.items()},
    }


# Dedektif Modu 2. adım: seçilen temaya (ör. "drought") uygun bölge + değişken
# önerileri, D'nin suggest() fonksiyonundan. Verisi olmayan öneriler elenir.
@app.get("/api/suggest")
def suggest(theme: str) -> list[dict]:
    if theme not in detective.THEMES:
        raise HTTPException(404, f"Unknown theme: {theme}")
    pairs = set(data_loader.available_pairs())
    return [s for s in detective.suggest(theme) if (s["region_id"], s["variable_id"]) in pairs]


# Dashboard'daki "Genel bakış" ızgarası için: verisi olan her bölge + değişken
# çiftinin trend özeti ve küçük çizgi grafik (sparkline) için yıllık ortalamaları.
# Veri yetersiz olan çiftler "error" alanıyla döner, ızgara bozulmaz.
@app.get("/api/overview")
def overview() -> list[dict]:
    items = []
    for region, variable in data_loader.available_pairs():
        item: dict = {"region_id": region, "variable_id": variable}
        try:
            series, result = _analyse(region, variable)
        except ValueError as err:
            item["error"] = str(err)
            items.append(item)
            continue
        yearly = series.groupby(series.index.year).agg(["mean", "count"])
        yearly = yearly[yearly["count"] >= 10]["mean"]  # skip years with many gaps
        item.update({
            "slope_per_decade": _num(result["slope_per_decade"]),
            "percent_change_per_decade": _num(result["percent_change_per_decade"]),
            "significant": bool(result["significant"]),
            "direction": result["direction"],
            "mk_p": _num(result["mk_p"]),
            "yearly": [{"year": int(y), "value": _num(v)} for y, v in yearly.items()],
        })
        items.append(item)
    return items


# Derlenmiş React arayüzü (frontend/dist) varsa onu da bu sunucudan yayınlar;
# böylece canlıya tek bir servis olarak alınabilir.
_DIST = ROOT / "frontend" / "dist"
if _DIST.exists():
    app.mount("/", StaticFiles(directory=_DIST, html=True), name="frontend")
