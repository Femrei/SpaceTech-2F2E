"""Haritadaki şehir adları için cities.js üretir.

Kaynak: Natural Earth 10m populated places (kamu malı),
https://github.com/nvkelso/natural-earth-vector (geojson/ne_10m_populated_places_simple.geojson).
Türkiye'deki yerleşimler alınır, birkaç ad Türkçeleştirilir ve listede olmayan bazı il
merkezleri ile birkaç ilçe (Çumra, Erciş) elle eklenir.

Kullanım (repo kökünden):  python detective3d/build_cities.py
"""
import json
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
URL = ("https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/"
       "ne_10m_populated_places_simple.geojson")
CACHE = HERE / "ne_raw" / "ne_10m_populated_places_simple.geojson"

RENAME = {"Istanbul": "İstanbul", "Icel": "Mersin", "Corum": "Çorum", "Afyon": "Afyonkarahisar",
          "Samandagi": "Samandağ"}
# Province centres missing from Natural Earth + a few towns: (name, lat, lon, min_zoom, population)
EXTRA = [
    ("Aksaray", 38.3687, 34.0370, 6.1, 230000), ("Osmaniye", 37.0742, 36.2478, 6.7, 280000),
    ("Düzce", 40.8438, 31.1565, 6.7, 200000), ("Yalova", 40.6500, 29.2667, 6.7, 150000),
    ("Bartın", 41.6344, 32.3375, 7, 80000), ("Iğdır", 39.9237, 44.0450, 7, 90000),
    ("Bayburt", 40.2552, 40.2249, 7, 50000), ("Ardahan", 41.1105, 42.7022, 7, 25000),
    ("Şırnak", 37.5164, 42.4611, 7, 70000),
    ("Çumra", 37.5730, 32.7740, 7, 66000), ("Erciş", 39.0280, 43.3590, 7, 100000),
]


def main():
    if not CACHE.exists():
        CACHE.parent.mkdir(exist_ok=True)
        with urllib.request.urlopen(URL, timeout=120) as r:
            CACHE.write_bytes(r.read())
    data = json.loads(CACHE.read_text(encoding="utf-8"))
    cities = []
    for f in data["features"]:
        p = f["properties"]
        if p.get("iso_a2") != "TR" and p.get("adm0name") != "Turkey":
            continue
        cities.append({"name": RENAME.get(p["name"], p["name"]), "lat": round(p["latitude"], 4),
                       "lon": round(p["longitude"], 4), "min_zoom": p.get("min_zoom") or 7,
                       "pop": int(p.get("pop_max") or 0),
                       "capital": p.get("featurecla") in ("Admin-0 capital", "Admin-1 capital")})
    names = {c["name"] for c in cities}
    for name, lat, lon, mz, pop in EXTRA:
        if name not in names:
            cities.append({"name": name, "lat": lat, "lon": lon, "min_zoom": mz, "pop": pop, "capital": False})
    cities.sort(key=lambda c: -c["pop"])
    (HERE / "cities.js").write_text("window.CITIES = " + json.dumps(cities, ensure_ascii=False) + ";\n",
                                    encoding="utf-8")
    print(len(cities), "cities written to cities.js")


if __name__ == "__main__":
    main()
