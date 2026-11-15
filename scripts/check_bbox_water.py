"""How much of each region box is sea or lake?

Giovanni's area average uses every grid cell in the box that has data. IMERG
precipitation and MERRA-2 temperature also have values over water, so a box
that reaches into the sea or covers a lake mixes water cells into the average.
This script measures that share with Natural Earth 10m land and lake polygons
(public domain) on a 300 x 300 sample grid, weighted by cos(latitude).

Usage (repo root):  python scripts/check_bbox_water.py
The two Natural Earth files (~20 MB) are downloaded once into data/cache/ (git-ignored).
"""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "cache"
BASE = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/"
GRID = 300


def _edges(name: str) -> np.ndarray:
    """All polygon ring edges of a Natural Earth layer as rows x1, y1, x2, y2."""
    path = CACHE / name
    if not path.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(BASE + name, timeout=180) as r:
            path.write_bytes(r.read())
    segs = []
    for feature in json.loads(path.read_text(encoding="utf-8"))["features"]:
        geom = feature["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        for poly in polys:
            for ring in poly:  # outer ring and holes: the even-odd rule handles both
                a = np.asarray(ring, dtype=float)[:, :2]
                segs.append(np.hstack([a[:-1], a[1:]]))
    return np.vstack(segs)


def share_inside(edges: np.ndarray, box: dict) -> float:
    """Share (0-1) of the box covered by the polygons, by ray casting towards the east."""
    x1, y1, x2, y2 = edges[(np.maximum(edges[:, 1], edges[:, 3]) >= box["south"])
                           & (np.minimum(edges[:, 1], edges[:, 3]) <= box["north"])
                           & (np.maximum(edges[:, 0], edges[:, 2]) >= box["west"])].T
    ys = box["south"] + (np.arange(GRID) + 0.5) / GRID * (box["north"] - box["south"])
    xs = box["west"] + (np.arange(GRID) + 0.5) / GRID * (box["east"] - box["west"])
    inside = total = 0.0
    for y in ys:
        cross = (y1 > y) != (y2 > y)
        xc = x1[cross] + (y - y1[cross]) * (x2[cross] - x1[cross]) / (y2[cross] - y1[cross])
        hit = (xc[None, :] > xs[:, None]).sum(axis=1) % 2 == 1
        weight = np.cos(np.radians(y))
        inside += weight * hit.sum()
        total += weight * GRID
    return inside / total


def main() -> None:
    land, lakes = _edges("ne_10m_land.geojson"), _edges("ne_10m_lakes.geojson")
    regions = json.loads((ROOT / "data" / "catalog.json").read_text(encoding="utf-8"))["regions"]
    print(f"{'region':10s} {'sea %':>6s} {'lake %':>7s}   box (W, S, E, N)")
    for region in regions:
        box = region["bbox"]
        sea = 1 - share_inside(land, box)
        lake = share_inside(lakes, box)
        print(f"{region['id']:10s} {100 * sea:6.1f} {100 * lake:7.1f}   "
              f"{box['west']}, {box['south']}, {box['east']}, {box['north']}")


if __name__ == "__main__":
    main()
