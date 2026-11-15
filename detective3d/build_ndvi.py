"""MODIS NDVI (MOD13Q1, 250 m, 16 günlük) 2001–2025 trendini üretir. Earthdata hesabı gerekmez.

Kaynak: ORNL DAAC "MODIS/VIIRS Land Product Subsets" web servisi
(https://modis.ornl.gov/data/modis_webservice.html). Servis istek başına en çok 10 tarih verir,
bu yüzden seri parça parça indirilir ve parçalar ndvi_raw/ klasöründe saklanır. Tekrar
çalıştırınca inen parçalar yeniden istenmez.

Neden bölge kutusunun tamamı değil?
250 m'de 2°×1.4°'lik kutu milyonlarca piksel demek. Bunun yerine her bölgede, MODIS arazi
örtüsüne (MCD12Q1, IGBP) göre seçilmiş 10 km × 10 km'lik bir "tarım penceresi" kullanılır.
Karadeniz kutusunda IGBP tarım sınıfı yok (çay/fındık bahçeleri orman/odunsu savan sayılıyor),
bu yüzden oradaki pencere bitki örtüsü penceresi olarak etiketlenir.

Yöntem:
- Her 16 günlük kompozitte penceredeki geçerli piksellerin ortalama NDVI'si alınır (ölçek 0.0001).
- Aylık değer = o aya düşen kompozitlerin en yükseği (maximum-value composite, bulut etkisini azaltır).
- Trend: repodaki B'nin analyze_trend fonksiyonu (mevsimsel Mann-Kendall + Sen), salt-okunur.
- Ek olarak her yılın en yüksek NDVI'si (yeşillenme zirvesi) için Mann-Kendall + Sen.

Kullanım:  .venv/Scripts/python build_ndvi.py ../SpaceTech-2F2E
"""
import collections
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
import pymannkendall as mk  # noqa: E402
from src import trend  # noqa: E402
os.chdir(_cwd)

API = "https://modis.ornl.gov/rst/api/v1"
PRODUCT, BAND, KM = "MOD13Q1", "250m_16_days_NDVI", 5     # 5 km each side -> ~10 km × 10 km
START, END = "2001-01-01", "2025-12-31"
RAW = HERE / "ndvi_raw"
RAW.mkdir(exist_ok=True)

# region -> (lat, lon, site name, kind). Chosen with MCD12Q1 land cover (see README).
SITES = {
    "konya": (37.57, 32.77, "Çumra ovası", "tarım"),
    "van": (39.03, 43.35, "Erciş ovası", "tarım"),
    "black_sea": (40.97, 40.55, "Rize kıyı yamaçları", "bitki örtüsü"),
}
IGBP = {1: "iğne yapraklı orman", 2: "geniş yapraklı yaprak dökmeyen orman", 4: "geniş yapraklı yaprak döken orman",
        5: "karışık orman", 8: "odunsu savan", 9: "savan", 10: "çayır/mera", 11: "sulak alan", 12: "tarım alanı",
        13: "yerleşim", 14: "tarım/doğal karışık", 16: "çıplak arazi", 17: "su"}


def get_json(url, cache: Path | None = None):
    if cache and cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=240) as r:
                text = r.read().decode("utf-8")
            data = json.loads(text)
            if cache:
                cache.write_text(text, encoding="utf-8")
            return data
        except Exception as err:
            print(f"  retry {attempt + 1}: {err} :: {url[-90:]}", flush=True)
            time.sleep(10 * (attempt + 1))
    raise RuntimeError(f"ORNL request failed: {url}")


def chunks_for(region):
    lat, lon, *_ = SITES[region]
    dates = get_json(f"{API}/{PRODUCT}/dates?latitude={lat}&longitude={lon}", RAW / f"{region}_dates.json")["dates"]
    dates = [d for d in dates if START <= d["calendar_date"] <= END]
    return [(region, dates[i]["modis_date"], dates[min(i + 9, len(dates) - 1)]["modis_date"])
            for i in range(0, len(dates), 10)]


def fetch_chunk(job):
    region, d0, d1 = job
    lat, lon, *_ = SITES[region]
    url = (f"{API}/{PRODUCT}/subset?latitude={lat}&longitude={lon}&band={BAND}"
           f"&startDate={d0}&endDate={d1}&kmAboveBelow={KM}&kmLeftRight={KM}")
    data = get_json(url, RAW / f"{region}_{d0}_{d1}.json")
    out = []
    for t in data["subset"]:
        vals = [v for v in t["data"] if v > -2000]  # -3000 = fill
        out.append((t["calendar_date"], float(np.mean(vals)) * 0.0001 if vals else None, len(vals), len(t["data"])))
    return out


def land_cover(region):
    lat, lon, *_ = SITES[region]
    url = (f"{API}/MCD12Q1/subset?latitude={lat}&longitude={lon}&band=LC_Type1"
           f"&startDate=A2020001&endDate=A2020001&kmAboveBelow={KM}&kmLeftRight={KM}")
    t = get_json(url, RAW / f"{region}_landcover2020.json")["subset"][0]
    c = collections.Counter(t["data"])
    n = sum(c.values())
    return [{"class": IGBP.get(k, str(k)), "igbp": k, "percent": round(v / n * 100)} for k, v in c.most_common(4)]


def clean(res):
    out = {}
    for k in ("sen_slope_per_decade", "ci_low", "ci_high", "significant", "direction", "mk_p",
              "percent_change_per_decade", "mean_value"):
        v = res.get(k)
        if isinstance(v, (bool, np.bool_)):
            out[k] = bool(v)
        elif isinstance(v, (int, float, np.floating, np.integer)):
            out[k] = None if math.isnan(float(v)) or math.isinf(float(v)) else float(v)
        else:
            out[k] = v
    return out


def main():
    jobs = [j for r in SITES for j in chunks_for(r)]
    todo = [j for j in jobs if not (RAW / f"{j[0]}_{j[1]}_{j[2]}.json").exists()]
    print(f"{len(jobs)} chunks, {len(todo)} to download (~30 s each)", flush=True)
    done = 0

    # NDVI_PARTIAL=1: no new chunk downloads; write results for the regions that are complete
    # in ndvi_raw/ and list the rest under "missing_regions".
    partial = os.environ.get("NDVI_PARTIAL") == "1"

    def run(job):
        nonlocal done
        if partial and not (RAW / f"{job[0]}_{job[1]}_{job[2]}.json").exists():
            return job[0], None
        try:
            res = fetch_chunk(job)
        except RuntimeError as err:  # ORNL gave up on this chunk: skip it, retry in the next pass
            print(f"  skipped for now: {err}", flush=True)
            return job[0], None
        done += 1
        if done % 10 == 0:
            print(f"  {done}/{len(jobs)} chunks", flush=True)
        return job[0], res

    # ORNL returns 502s under load; a few passes with fewer parallel requests get everything.
    workers = int(os.environ.get("NDVI_WORKERS", 3))
    for attempt in range(1 if partial else int(os.environ.get("NDVI_PASSES", 6))):
        with ThreadPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(run, jobs))
        missing = [j for j, (_, res) in zip(jobs, results) if res is None]
        if not missing or partial:
            break
        print(f"pass {attempt + 1}: {len(missing)} chunks still missing, waiting 60 s before the next pass", flush=True)
        done = len(jobs) - len(missing)
        time.sleep(60)
    incomplete = sorted({j[0] for j in missing})
    if incomplete and not partial:
        print(f"Still missing {len(missing)} chunks; run again later, or with NDVI_PARTIAL=1 "
              f"to write the complete regions only.", flush=True)
        sys.exit(1)
    for region in incomplete:
        have = sum(1 for j in jobs if j[0] == region and j not in missing)
        total = sum(1 for j in jobs if j[0] == region)
        print(f"skipping {region}: {have}/{total} chunks downloaded", flush=True)

    months = pd.date_range(START, END, freq="MS")
    out = {"product": f"{PRODUCT} v061 · {BAND}", "months": [m.strftime("%Y-%m") for m in months],
           "window_km": 2 * KM, "sites": {}, "series": {},
           "missing_regions": {r: {"name": SITES[r][2], "lat": SITES[r][0], "lon": SITES[r][1]} for r in incomplete},
           "source": {"dataset": "MODIS Terra MOD13Q1 v061 NDVI (250 m, 16-day) via ORNL DAAC Land Product Subsets",
                      "url": "https://modis.ornl.gov/data/modis_webservice.html", "via": "ORNL DAAC"}}
    for region, (lat, lon, name, kind) in SITES.items():
        if region in incomplete:
            continue
        comp = sorted(x for r, res in results if r == region for x in res)
        s = pd.Series({pd.Timestamp(d): v for d, v, _, _ in comp if v is not None})
        monthly = s.groupby(s.index.to_period("M")).max()           # maximum-value composite
        monthly.index = monthly.index.to_timestamp()
        monthly = monthly.reindex(months)
        res = trend.analyze_trend(monthly.dropna())
        peak = monthly.groupby(monthly.index.year).max().dropna()
        pk = mk.original_test(peak.values)
        valid_share = float(np.mean([n / tot for _, _, n, tot in comp if tot])) if comp else None
        out["sites"][region] = {"lat": lat, "lon": lon, "name": name, "kind": kind, "land_cover": land_cover(region),
                                "composites": len(comp), "valid_pixel_share": round(valid_share, 3)}
        out["series"][region] = {
            "values": [None if pd.isna(v) else round(float(v), 4) for v in monthly],
            "trend": clean(res),
            "peak": {"years": [int(y) for y in peak.index], "values": [round(float(v), 4) for v in peak.values],
                     "sen_slope_per_decade": float(pk.slope) * 10, "mk_p": float(pk.p),
                     "significant": bool(pk.p < 0.05), "direction": pk.trend},
        }
        t, pkd = out["series"][region]["trend"], out["series"][region]["peak"]
        print(f"{region:10s} {name:22s} monthly {t['sen_slope_per_decade']:+.4f}/10y p={t['mk_p']:.1e} | "
              f"peak {pkd['sen_slope_per_decade']:+.4f}/10y p={pkd['mk_p']:.1e} | LC {out['sites'][region]['land_cover'][:2]}",
              flush=True)

    dest = HERE / "ndvi_data.js"
    dest.write_text("window.NDVI_DATA = " + json.dumps(out, ensure_ascii=False) + ";\n", encoding="utf-8")
    print("written:", dest, flush=True)


if __name__ == "__main__":
    main()
