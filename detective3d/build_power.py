"""NASA POWER 1981–2025 "uzun kayıt" verisini indirir ve B'nin trend analiziyle işler.

- Her bölge kutusunun içindeki POWER ızgara hücresi merkezlerinden (MERRA-2 ızgarası,
  0.5° enlem × 0.625° boylam) aylık veri çekilir ve noktaların ortalaması alınır.
  POWER'ın "regional" sorgusu en az 2° enlem istediği için nokta sorgusu kullanılır.
- Ham yanıtlar power_raw/ klasöründe saklanır (tekrar çalıştırınca yeniden indirilmez).
- Trend: repodaki src.trend.analyze_trend (B), salt-okunur. 1981–2025 ve 2001–2025
  için ayrı ayrı hesaplanır.
- Çıktı: power_data.js (window.POWER_DATA).

Kullanım:  .venv/Scripts/python build_power.py ../SpaceTech-2F2E
"""
import json
import math
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = Path(sys.argv[1] if len(sys.argv) > 1 else HERE.parent / "SpaceTech-2F2E").resolve()
sys.path.insert(0, str(REPO))
_cwd = os.getcwd()
os.chdir(REPO)
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from src import detective, trend  # noqa: E402
os.chdir(_cwd)

START, END = 1981, 2025
RAW = HERE / "power_raw"
RAW.mkdir(exist_ok=True)
API = ("https://power.larc.nasa.gov/api/temporal/monthly/point?parameters=T2M,T2M_MAX,PRECTOTCORR,GWETROOT"
       "&community=AG&longitude={lon}&latitude={lat}&start={start}&end={end}&format=JSON")

# id -> (POWER parameter, label, unit, converter(monthly value, days in month))
VARS = {
    "T2M": ("Hava sıcaklığı (2 m)", "°C", lambda v, d: v),
    "T2M_MAX": ("Günlük en yüksek sıcaklık ort.", "°C", lambda v, d: v),
    "PRECTOTCORR": ("Yağış (düzeltilmiş)", "mm/ay", lambda v, d: v * d),     # mm/day -> mm/month
    "GWETROOT": ("Kök bölgesi toprak ıslaklığı", "%", lambda v, d: v * 100),  # 0–1 -> %
}


def grid_points(b):
    lats = np.arange(b["south"] + 0.25, b["north"], 0.5)
    lons = np.arange(b["west"] + 0.3125, b["east"], 0.625)
    return [(round(float(la), 4), round(float(lo), 4)) for la in lats for lo in lons]


def fetch(region, lat, lon):
    path = RAW / f"{region}_{lat}_{lon}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    url = API.format(lat=lat, lon=lon, start=START, end=END)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                data = json.loads(r.read().decode("utf-8"))
            path.write_text(json.dumps(data), encoding="utf-8")
            return data
        except Exception as err:  # network hiccup / rate limit: back off and retry
            print(f"  retry {attempt + 1} {region} {lat},{lon}: {err}")
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"POWER download failed for {region} {lat},{lon}")


def to_series(data, param):
    fill = data["header"].get("fill_value", -999)
    vals = {k: v for k, v in data["properties"]["parameter"][param].items() if not k.endswith("13")}
    s = pd.Series(vals, dtype=float)
    s.index = pd.to_datetime(s.index, format="%Y%m")
    return s.where(s != fill)


def scalars(res):
    keys = ("sen_slope_per_decade", "ci_low", "ci_high", "significant", "direction", "mk_p",
            "percent_change_per_decade", "mean_value", "years_needed_estimate")
    out = {}
    for k in keys:
        v = res.get(k)
        if isinstance(v, (bool, np.bool_)):
            out[k] = bool(v)
        elif isinstance(v, (int, float, np.floating, np.integer)):
            v = float(v)
            out[k] = None if math.isnan(v) or math.isinf(v) else v
        else:
            out[k] = v
    return out


def main():
    regions = detective.load_catalog()["regions"]
    jobs = [(r["id"], la, lo) for r in regions for la, lo in grid_points(r["bbox"])]
    print(f"{len(jobs)} POWER points to load")
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(lambda j: (j, fetch(*j)), jobs))

    months = pd.date_range(f"{START}-01-01", f"{END}-12-01", freq="MS")
    out = {"start": START, "end": END, "months": [m.strftime("%Y-%m") for m in months],
           "variables": {k: {"label": v[0], "unit": v[1]} for k, v in VARS.items()},
           "points": {}, "series": {},
           "source": {"name": "NASA POWER (LaRC), monthly point API, community=AG",
                      "url": "https://power.larc.nasa.gov/docs/services/api/temporal/monthly/",
                      "note": "Area mean of the POWER grid-cell centres inside each region box "
                              "(MERRA-2 ~0.5°×0.625° for meteorology; PRECTOTCORR is bias-corrected precipitation)."}}
    for r in regions:
        rid = r["id"]
        pts = [(j, d) for j, d in results if j[0] == rid]
        out["points"][rid] = [[j[1], j[2]] for j, _ in pts]
        for param, (_, _, conv) in VARS.items():
            mean = pd.concat([to_series(d, param) for _, d in pts], axis=1).mean(axis=1)
            mean = mean.reindex(months)
            mean = pd.Series([None if pd.isna(v) else conv(v, m.days_in_month) for m, v in mean.items()],
                             index=months, dtype=float)
            full = trend.analyze_trend(mean.dropna())
            recent = trend.analyze_trend(mean[mean.index.year >= 2001].dropna())
            out["series"][f"{rid}|{param}"] = {
                "values": [None if pd.isna(v) else round(float(v), 3) for v in mean],
                "full": scalars(full), "recent": scalars(recent),
            }
            f, rc = out["series"][f"{rid}|{param}"]["full"], out["series"][f"{rid}|{param}"]["recent"]
            print(f"{rid:10s} {param:12s} 1981-2025 {f['sen_slope_per_decade']:+.3f} p={f['mk_p']:.1e} | "
                  f"2001-2025 {rc['sen_slope_per_decade']:+.3f} p={rc['mk_p']:.1e}")

    dest = HERE / "power_data.js"
    dest.write_text("window.POWER_DATA = " + json.dumps(out, ensure_ascii=False) + ";\n", encoding="utf-8")
    print("written:", dest)


if __name__ == "__main__":
    main()
