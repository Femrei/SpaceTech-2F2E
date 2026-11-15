"""Earth Trend Detective: FastAPI backend (owner: C).

Wraps teammates' Python modules (A: data_loader, B: trend, D: detective) in a
small JSON API for the React frontend in ``frontend/``. Teammates' code is
used unchanged.

Dev:   uvicorn api:app --reload            (frontend: cd frontend && npm run dev)
Prod:  cd frontend && npm run build, then  uvicorn api:app
       (the built frontend in frontend/dist is served by this same app)
"""
from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent


from src import data_loader, detective, trend  # A, D, B (all on main now)
import power_loader  # EXPERIMENT: "Pick a place" tab (NASA POWER); remove with /api/point + /api/box

# A's processed CSV is built from the raw Giovanni downloads in data/raw/. If there
# are none, the CSV can only have come from B's `python -m src.mock_data`, so the
# numbers are synthetic and the UI must say so.
MOCK_DATA = not any((ROOT / "data" / "raw").glob("*.csv"))

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


# B'nin trend_line'ı gerçek birimdedir (uzun dönem ortalama eklenmiş). Grafiklerde
# anomali ölçeğinde (0 etrafında) bir çizgi gerekir; ortalamayı çıkararak onu elde eder.
# Arayüz "Basit" görünümde ortalamayı geri ekler.
def _anomaly_trend(result: dict) -> pd.Series:
    return result["trend_line"] - result["mean_value"]


# Güven bandını hesaplar: trend çizgisinin (anomali ölçeğinde) orta noktasından geçen,
# eğimleri ci_low ve ci_high olan iki doğru. Orta noktadan uçlara doğru yelpaze gibi açılır.
def _ci_fan(result: dict) -> tuple[pd.Series, pd.Series]:
    trend_line = _anomaly_trend(result).dropna()
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
# sözlük, ipuçları), temalar, verisi olan çiftler, veri indirme tarihi, stub listesi.
@app.get("/api/meta")
def meta() -> dict:
    catalog = detective.load_catalog()
    return {
        "variables": catalog["variables"],
        "regions": catalog["regions"],
        "glossary": detective.glossary(),
        "themes": detective.THEMES,
        # D's hint rules, so the UI can show its own translation of the matched rule.
        "hints": catalog.get("hints", []),
        "pairs": [list(p) for p in data_loader.available_pairs()],
        "data_downloaded_on": data_loader.DATA_DOWNLOADED_ON,
        "mock_data": MOCK_DATA,
        # B: "% change" is meaningless on an interval scale such as °C; hide it for these.
        "no_percent_variables": sorted(getattr(trend, "NO_PERCENT_VARIABLES", ())) + [
            vid for vid, v in power_loader.POINT_VARIABLES.items()
            if v["interpret_as"] in getattr(trend, "NO_PERCENT_VARIABLES", ())
        ],
        # EXPERIMENT: variables offered in the "Pick a place" tab (NASA POWER).
        "point_variables": [
            {"id": vid, "name": v["name"], "unit": v["unit"], "short_description": v["short_description"],
             "dataset": "NASA POWER (MERRA-2)", "period": {"start": f"{power_loader.START_YEAR}-01",
                                                         "end": f"{power_loader.END_YEAR}-12"},
             "long_description": "", "themes": []}
            for vid, v in power_loader.POINT_VARIABLES.items()
        ],
    }


# 12 aylık hareketli ortalama. Sadece tam 12 aylık pencere kullanılır: kenarlarda
# yarım pencere mevsim etkisiyle sahte bir sıçrama gösterirdi. Serinin içindeki tek
# tük boş aylar önce komşularından doldurulur ki ortalamada 12 aylık delik açmasın.
def _smooth12(series: pd.Series) -> pd.Series:
    return (series.interpolate(limit_area="inside")
            .rolling(12, center=True, min_periods=12).mean())


# Trend sonucundaki tek değerli alanları (Series olmayanları) JSON'a uygun tiplere çevirir.
# Başlangıç/bitiş tarihleri "YYYY-MM-DD" metnine çevrilir; kolaylık olsun diye
# start_year / end_year alanları da eklenir.
def _scalars(result: dict) -> dict:
    stats = {}
    for k, v in result.items():  # Series go into the chart points instead
        if isinstance(v, pd.Series):
            continue
        if isinstance(v, pd.Timestamp):
            stats[k] = v.strftime("%Y-%m-%d")
            stats[f"{k}_year"] = int(v.year)
        elif isinstance(v, (bool, np.bool_)):
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
# B'nin interpret() metni ve D'nin next_step() ipucu (metin + takip edilecek
# değişken/bölge; "ipucunu takip et" butonu bunu kullanır).
@app.get("/api/analysis")
def analysis(region: str, variable: str) -> dict:
    region_info, variable_info, series, result = _checked(region, variable)
    return {
        "points": _chart_points(series, result),
        "result": _scalars(result),
        # B: interpret(result, variable_id, region_name); D's name_in_text reads
        # naturally in a sentence ("in the Konya Closed Basin").
        "interpretation": trend.interpret(result, variable, region_info.get("name_in_text", region_info["name"])),
        "next_step": detective.next_step(result, variable, region),
    }


# Grafik için aylık noktalar: ham değer, 12 aylık ortalama, anomali, eğilim (anomali
# ölçeğinde) ve güven bandı. Pano ve "Konumunu seç" sekmesi aynı biçimi kullanır.
def _chart_points(series: pd.Series, result: dict) -> list[dict]:
    smooth = _smooth12(series)
    trend_anom = _anomaly_trend(result)
    low, high = _ci_fan(result)
    return [
        {
            "date": d.strftime("%Y-%m-%d"),
            "value": _num(series.get(d)),
            "smooth": _num(smooth.get(d)),
            "anomaly": _num(result["anomalies"].get(d)),
            "trend": _num(trend_anom.get(d)),
            "ci_low": _num(low.get(d)),
            "ci_high": _num(high.get(d)),
        }
        for d in series.index
    ]


# Bir enlem/boylam aralığını cümlede okunur yazar: "37.00°N–39.00°N".
def _span(lo: float, hi: float, pos: str, neg: str) -> str:
    return f"{abs(lo):.2f}°{pos if lo >= 0 else neg}–{abs(hi):.2f}°{pos if hi >= 0 else neg}"


# EXPERIMENT – "Konumunu seç" sekmesinin "Nokta" modu: dünyadaki herhangi bir nokta için
# NASA POWER'dan 1981–2025 aylık seriyi (tek ızgara hücresi) çeker ve B'nin aynı
# analizini uygular. Cevap /api/analysis ile aynı biçimdedir (+ noktanın ve ızgara
# hücresinin bilgisi); D'nin ipucu kuralları katalogdaki bölgelere bağlı olduğu için
# burada ipucu yoktur.
@app.get("/api/point")
def point(lat: float, lon: float, variable: str) -> dict:
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise HTTPException(422, "Latitude must be within ±90 and longitude within ±180.")
    if variable not in power_loader.POINT_VARIABLES:
        raise HTTPException(404, f"Unknown variable {variable!r}.")
    try:
        series = power_loader.load_point_series(lat, lon, variable)
    except ValueError as err:  # e.g. soil wetness over open water
        raise HTTPException(422, str(err)) from err
    except power_loader.PowerError as err:
        raise HTTPException(502, str(err)) from err
    try:
        result = trend.analyze_trend(series)
    except ValueError as err:  # e.g. too few valid months
        raise HTTPException(422, str(err)) from err
    cell = power_loader.merra2_cell(lat, lon)
    place = f"the grid cell around {abs(lat):.2f}°{'N' if lat >= 0 else 'S'}, {abs(lon):.2f}°{'E' if lon >= 0 else 'W'}"
    return {
        "points": _chart_points(series, result),
        "result": _scalars(result),
        "interpretation": trend.interpret(result, power_loader.POINT_VARIABLES[variable]["interpret_as"], place),
        "next_step": {"text": "", "text_tr": "", "variable_id": None, "region_id": None},
        "point": {"lat": lat, "lon": lon, "cell": cell, "n_cells": 1,
                  "cells": [[(cell["south"] + cell["north"]) / 2, (cell["west"] + cell["east"]) / 2]],
                  "source": power_loader.POINT_SOURCE},
    }


# EXPERIMENT – "Konumunu seç" sekmesi ("Kare çiz"): kullanıcının haritada çizdiği
# kutunun (güney, batı, kuzey, doğu) NASA POWER alan ortalamasını B'nin aynı
# analizinden geçirir. Kutunun kenarları en fazla 10 derece olabilir (POWER kuralı).
# Cevap /api/analysis ile aynı biçimdedir; ek olarak "point" alanında kullanılan
# hücreler ve kaynak bulunur. D'nin ipucu kuralları katalogdaki bölgelere bağlı
# olduğu için burada ipucu yoktur.
@app.get("/api/box")
def box(south: float, west: float, north: float, east: float, variable: str) -> dict:
    if not (-90 <= south < north <= 90 and -180 <= west < east <= 180):
        raise HTTPException(422, "Give the box as south < north (±90) and west < east (±180).")
    if variable not in power_loader.POINT_VARIABLES:
        raise HTTPException(404, f"Unknown variable {variable!r}.")
    try:
        loaded = power_loader.load_box_series(south, west, north, east, variable)
    except ValueError as err:  # box too large, or soil wetness over open water only
        raise HTTPException(422, str(err)) from err
    except power_loader.PowerError as err:
        raise HTTPException(502, str(err)) from err
    series = loaded["series"]
    try:
        result = trend.analyze_trend(series)
    except ValueError as err:  # e.g. too few valid months
        raise HTTPException(422, str(err)) from err
    area = loaded["area"]
    place = f"the box {_span(south, north, 'N', 'S')}, {_span(west, east, 'E', 'W')}"
    return {
        "points": _chart_points(series, result),
        "result": _scalars(result),
        "interpretation": trend.interpret(result, power_loader.POINT_VARIABLES[variable]["interpret_as"], place),
        "next_step": {"text": "", "variable_id": None, "region_id": None},
        "point": {"lat": (area["south"] + area["north"]) / 2, "lon": (area["west"] + area["east"]) / 2,
                  "cell": area, "n_cells": loaded["n_cells"], "cells": loaded["cells"],
                  "source": power_loader.BOX_SOURCE},
    }


# Karşılaştır sekmesinin verisi: aynı değişken için iki bölgenin anomalileri
# (12 aylık ortalaması alınmış, okunaklı olsun diye) ve trend çizgileri,
# iki bölgenin istatistikleri ve B'nin compare_trends() özeti.
@app.get("/api/compare")
def compare(variable: str, region_a: str, region_b: str) -> dict:
    _, _, _, res_a = _checked(region_a, variable)
    _, _, _, res_b = _checked(region_b, variable)
    smooth_a, smooth_b = _smooth12(res_a["anomalies"]), _smooth12(res_b["anomalies"])
    trend_a, trend_b = _anomaly_trend(res_a), _anomaly_trend(res_b)
    index = res_a["anomalies"].index.union(res_b["anomalies"].index)
    points = [
        {
            "date": d.strftime("%Y-%m-%d"),
            "a": _num(smooth_a.get(d)),
            "b": _num(smooth_b.get(d)),
            "trend_a": _num(trend_a.get(d)),
            "trend_b": _num(trend_b.get(d)),
        }
        for d in index
    ]
    summary = trend.compare_trends(res_a, res_b)  # B: compare_trends(result_a, result_b)
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
            "sen_slope_per_decade": _num(result["sen_slope_per_decade"]),
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
