"""EXPERIMENT (owner: C): monthly series for any point or box on Earth from NASA POWER.

NASA POWER (https://power.larc.nasa.gov) serves MERRA-2-based monthly values on a
0.5° x 0.625° grid with no API key. This module returns either one grid cell (a
point) or the area-weighted average of the cells inside a user-drawn box (like
Giovanni's area average), in the same shape as A's ``load_series`` output (a monthly
``pd.Series`` with freq "MS"), so B's ``analyze_trend`` runs on it unchanged.

Not part of the agreed data pipeline (that is A's Giovanni data); used only by the
"Pick a place" tab. Delete this file and the /api/point + /api/box endpoints to remove it.
"""
from __future__ import annotations

import calendar
import json
import urllib.error
import urllib.parse
import urllib.request
from functools import lru_cache

import numpy as np
import pandas as pd

POWER_URL = "https://power.larc.nasa.gov/api/temporal/monthly/point"
POWER_REGIONAL_URL = "https://power.larc.nasa.gov/api/temporal/monthly/regional"
# POWER's regional endpoint: each side must span 2–10 degrees, one parameter per request.
REGIONAL_MIN_DEG = 2.0
REGIONAL_MAX_DEG = 10.0
START_YEAR = 1981
END_YEAR = 2025
POINT_SOURCE = "NASA POWER (MERRA-2), monthly, single grid cell"
BOX_SOURCE = "NASA POWER (MERRA-2), monthly, area-weighted average of the grid cells inside the drawn box"

# Variables offered in the "Pick a place" tab: POWER parameter, display name, unit, short text.
# interpret_as: the variable id passed to B's trend.interpret() so the sentence gets
# the right name/unit and temperature gets no % change.
POINT_VARIABLES: dict[str, dict] = {
    "power_temp": {
        "interpret_as": "temp",
        "parameter": "T2M",
        "name": "Air temperature (2 m)",
        "unit": "°C",
        "short_description": "How warm the air is about 2 metres above the ground.",
    },
    "power_precip": {
        "interpret_as": "precip",
        "parameter": "PRECTOTCORR",
        "name": "Precipitation",
        "unit": "mm/month",
        "short_description": "How much rain and snow falls each month (MERRA-2, bias-corrected).",
    },
    "power_soil_wetness": {
        "interpret_as": "surface_soil_wetness",
        "parameter": "GWETTOP",
        "name": "Surface soil wetness",
        "unit": "percentage points",  # the value is already a %, so changes are in points
        "short_description": "How close the top soil layer is to being fully saturated: 0% bone dry, 100% saturated.",
    },
}


class PowerError(RuntimeError):
    """NASA POWER could not be reached or returned no usable data."""


NO_LAND = "Soil wetness is only measured over land, and this place is open water. Pick a spot on land."


# Toprak ıslaklığında deniz hücresini tanır: POWER denizde her ay 1,0 (%100) verir.
# Bu hücreler ortalamaya girerse kıyıdaki alanlar yapay olarak "ıslak" görünür.
def _is_open_water(s: pd.Series, variable_id: str) -> bool:
    return variable_id == "power_soil_wetness" and bool((s.dropna() >= 99.9).all())


# POWER'a GET isteği atar ve JSON cevabı döndürür. Ağ hatasında ya da POWER bir
# hata mesajı döndürdüğünde (ör. 422 "en az 2 derece") PowerError fırlatır.
def _get_json(url: str, timeout: int = 60) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as err:
        try:
            detail = "; ".join(json.load(err).get("messages", [])) or str(err)
        except (json.JSONDecodeError, AttributeError):
            detail = str(err)
        raise PowerError(f"NASA POWER rejected the request: {detail}") from err
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as err:
        raise PowerError(f"NASA POWER request failed: {err}") from err


# POWER'dan bir nokta için tüm değişkenlerin aylık verisini tek istekte indirir.
# Aynı (yuvarlanmış) koordinat için sonuç bellekte tutulur; POWER'a tekrar gidilmez.
@lru_cache(maxsize=256)
def _fetch(lat: float, lon: float) -> dict:
    query = urllib.parse.urlencode({
        "parameters": ",".join(v["parameter"] for v in POINT_VARIABLES.values()),
        "community": "AG",
        "latitude": lat,
        "longitude": lon,
        "start": START_YEAR,
        "end": END_YEAR,
        "format": "JSON",
    })
    data = _get_json(f"{POWER_URL}?{query}", timeout=30)
    if "properties" not in data:
        raise PowerError(f"NASA POWER returned no data: {str(data)[:200]}")
    return data


# Noktanın düştüğü MERRA-2 ızgara hücresinin sınırlarını hesaplar (0,5° enlem x 0,625°
# boylam; hücre merkezleri -90 / -180'den başlar). POWER'ın aylık değerleri bu hücreye
# aittir; harita bu kutuyu "verinin geldiği alan" olarak çizer.
def merra2_cell(lat: float, lon: float) -> dict:
    c_lat = round((lat + 90) / 0.5) * 0.5 - 90
    c_lon = round((lon + 180) / 0.625) * 0.625 - 180
    return {"south": max(c_lat - 0.25, -90), "north": min(c_lat + 0.25, 90),
            "west": c_lon - 0.3125, "east": c_lon + 0.3125}


# Nokta modu: bir noktanın bir değişkeni için aylık seriyi A'nın load_series çıktısıyla
# aynı biçimde döndürür (aylık pd.Series, freq "MS"). Toprak ıslaklığında nokta açık
# denizdeyse ValueError fırlatır.
def load_point_series(lat: float, lon: float, variable_id: str) -> pd.Series:
    if variable_id not in POINT_VARIABLES:
        raise KeyError(variable_id)
    data = _fetch(round(lat, 2), round(lon, 2))
    raw = data["properties"]["parameter"][POINT_VARIABLES[variable_id]["parameter"]]
    s = _to_monthly(raw, variable_id)
    if _is_open_water(s, variable_id):
        raise ValueError(NO_LAND)
    s.name = variable_id
    return s


# POWER'ın bir hücre için döndürdüğü {"YYYYMM": değer} sözlüğünü aylık pd.Series'e
# çevirir: yıllık değerleri ("YYYY13") atar, -999 boş değerlerini NaN yapar, birimleri
# dönüştürür (yağış mm/gün -> mm/ay, toprak ıslaklığı 0–1 -> %).
# Not: POWER toprak ıslaklığını 2 ondalıkla (yani %1'lik adımlarla) verir.
def _to_monthly(raw: dict, variable_id: str) -> pd.Series:
    monthly = {k: v for k, v in raw.items() if not k.endswith("13")}  # "YYYY13" = annual value
    s = pd.Series(monthly, dtype=float)
    s.index = pd.to_datetime(s.index, format="%Y%m")
    s = s.sort_index().mask(s <= -999).asfreq("MS")  # -999 = POWER fill value

    if variable_id == "power_precip":
        days = np.array([calendar.monthrange(d.year, d.month)[1] for d in s.index])
        s = s * days
    elif variable_id == "power_soil_wetness":
        s = s * 100

    return s.round(4)  # remove float noise from the conversions (0.57 * 100 = 56.99999…)


# POWER'ın bölge servisinden bir kutudaki tüm ızgara hücrelerinin tek bir parametresini
# indirir. Kutu kenarları 2–10 derece olmalı (POWER kuralı). Sonuç bellekte tutulur.
@lru_cache(maxsize=64)
def _fetch_regional(south: float, west: float, north: float, east: float, parameter: str) -> dict:
    query = urllib.parse.urlencode({
        "parameters": parameter,
        "community": "AG",
        "latitude-min": south,
        "latitude-max": north,
        "longitude-min": west,
        "longitude-max": east,
        "start": START_YEAR,
        "end": END_YEAR,
        "format": "JSON",
    })
    data = _get_json(f"{POWER_REGIONAL_URL}?{query}")
    if not data.get("features"):
        raise PowerError(f"NASA POWER returned no data: {str(data)[:200]}")
    return data


# [lo, hi] aralığını POWER'ın en az 2 derecelik kuralına uyacak şekilde, ortasından
# genişletir ve [-limit, limit] içinde tutar (kenara dayanırsa diğer yöne kayar).
# Tam 2,0'a değil 2,1'e genişletir: ondalık yuvarlamayla 1,9999… çıkıp POWER'ın
# isteği reddetmesini önlemek için küçük bir pay bırakılır.
def _widen(lo: float, hi: float, limit: float) -> tuple[float, float]:
    need = REGIONAL_MIN_DEG + 0.1
    if hi - lo >= need:
        return lo, hi
    mid = (lo + hi) / 2
    lo, hi = mid - need / 2, mid + need / 2
    if lo < -limit:
        lo, hi = -limit, -limit + need
    if hi > limit:
        lo, hi = limit - need, limit
    return round(lo, 3), round(hi, 3)


# Kare modu: kullanıcının çizdiği kutunun (güney, batı, kuzey, doğu) bir değişken için
# alan ortalaması aylık serisini döndürür; Giovanni'deki bölge ortalamasının POWER karşılığı.
#   1) POWER'dan kutudaki hücreleri indirir (2 dereceden küçükse istek genişletilir).
#   2) Merkezi kutunun içinde kalan hücreleri seçer (kenarın tam üstündekiler dahil);
#      kutu tek hücreden bile küçükse kutunun ortasına en yakın hücreyi alır.
#   3) Toprak ıslaklığında deniz hücrelerini atar.
#   4) Hücreleri cos(enlem) ağırlığıyla ortalar: kuzeye gidildikçe hücrelerin alanı
#      küçüldüğü için her hücre kapladığı alan kadar sayılır (Giovanni'deki gibi).
# Dönen sözlük: series, n_cells (kullanılan hücre sayısı), cells (hücre merkezleri,
# haritada çizmek için) ve area (kullanılan hücrelerin kapladığı alanın sınırları).
def load_box_series(south: float, west: float, north: float, east: float, variable_id: str) -> dict:
    if variable_id not in POINT_VARIABLES:
        raise KeyError(variable_id)
    if north - south > REGIONAL_MAX_DEG or east - west > REGIONAL_MAX_DEG:
        raise ValueError(f"The box can be at most {REGIONAL_MAX_DEG:g} degrees on each side.")
    parameter = POINT_VARIABLES[variable_id]["parameter"]
    q_south, q_north = _widen(south, north, 90)
    q_west, q_east = _widen(west, east, 180)
    data = _fetch_regional(q_south, q_west, q_north, q_east, parameter)

    cells = []  # (lat, lon, raw dict)
    for f in data["features"]:
        lon, lat = f["geometry"]["coordinates"][:2]
        cells.append((lat, lon, f["properties"]["parameter"][parameter]))
    inside = [c for c in cells if south <= c[0] <= north and west <= c[1] <= east]
    if not inside:  # box smaller than one grid cell: use the cell closest to its centre
        c_lat, c_lon = (south + north) / 2, (west + east) / 2
        inside = [min(cells, key=lambda c: (c[0] - c_lat) ** 2 + (c[1] - c_lon) ** 2)]

    inside = [(lat, lon, _to_monthly(raw, variable_id)) for lat, lon, raw in inside]
    inside = [c for c in inside if not _is_open_water(c[2], variable_id)]
    if not inside:
        raise ValueError(NO_LAND)

    frame = pd.concat([s for _, _, s in inside], axis=1)
    weights = np.cos(np.radians([lat for lat, _, _ in inside]))
    values = frame.to_numpy()
    valid = ~np.isnan(values)
    weighted = np.where(valid, values, 0) @ weights
    total_w = valid @ weights
    mean = np.divide(weighted, total_w, out=np.full(len(frame), np.nan), where=total_w > 0)
    series = pd.Series(mean, index=frame.index, name=variable_id).round(4)

    lats = [lat for lat, _, _ in inside]
    lons = [lon for _, lon, _ in inside]
    area = {"south": max(min(lats) - 0.25, -90), "north": min(max(lats) + 0.25, 90),
            "west": min(lons) - 0.3125, "east": max(lons) + 0.3125}
    return {"series": series, "n_cells": len(inside), "cells": [[lat, lon] for lat, lon in zip(lats, lons)],
            "area": area}

