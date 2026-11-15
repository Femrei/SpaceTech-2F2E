"""Tests for the "Alan seç" (pick an area) endpoints of the 3D app server (owner: C).

detective3d/agent_server.py exposes /api/point and /api/box, which call C's
api.point() / api.box() on NASA POWER data. NASA POWER is replaced here by a
synthetic series, so the tests run offline and fast.

Run from the repo root:  python -m pytest -q
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
APP_DIR = ROOT / "detective3d"


# Sunucu modülünü dosyasından yükler (detective3d bir paket değil).
@pytest.fixture(scope="module")
def server():
    spec = importlib.util.spec_from_file_location("agent_server_area", APP_DIR / "agent_server.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# 1981–2025 aylık yapay seri: mevsim döngüsü + on yılda 0.5 birimlik artış.
def _fake_series() -> pd.Series:
    index = pd.date_range("1981-01-01", "2025-12-01", freq="MS")
    t = np.arange(len(index))
    values = 10 + 8 * np.sin(2 * np.pi * t / 12) + 0.5 * t / 120
    return pd.Series(values, index=index)


# NASA POWER yerine yapay seri döndüren test istemcisi.
@pytest.fixture()
def client(server, monkeypatch):
    loader = server.api.power_loader
    monkeypatch.setattr(loader, "load_point_series", lambda lat, lon, variable: _fake_series())
    monkeypatch.setattr(loader, "load_box_series", lambda s, w, n, e, variable: {
        "series": _fake_series(), "n_cells": 6, "cells": [[s + 0.25, w + 0.3125]] * 6,
        "area": {"south": s, "west": w, "north": n, "east": e},
    })
    return TestClient(server.app)


def test_point_endpoint(client):
    r = client.get("/api/point", params={"lat": 37.87, "lon": 32.49, "variable": "power_temp"})
    assert r.status_code == 200
    body = r.json()
    assert body["result"]["direction"] == "increasing"
    assert body["result"]["significant"] is True
    assert len(body["points"]) == 540
    assert body["point"]["n_cells"] == 1
    cell = body["point"]["cell"]
    assert cell["south"] <= 37.87 <= cell["north"] and cell["west"] <= 32.49 <= cell["east"]


def test_box_endpoint(client):
    r = client.get("/api/box", params={"south": 37, "west": 32, "north": 39, "east": 34,
                                       "variable": "power_precip"})
    assert r.status_code == 200
    body = r.json()
    assert body["point"]["n_cells"] == 6
    assert body["point"]["cell"] == {"south": 37, "west": 32, "north": 39, "east": 34}


@pytest.mark.parametrize("params", [
    {"south": 39, "west": 32, "north": 37, "east": 34, "variable": "power_temp"},  # south > north
    {"lat": 95, "lon": 32, "variable": "power_temp"},                              # latitude out of range
])
def test_bad_coordinates_are_rejected(client, params):
    path = "/api/box" if "south" in params else "/api/point"
    assert client.get(path, params=params).status_code == 422


def test_unknown_variable_is_404(client):
    r = client.get("/api/point", params={"lat": 37, "lon": 32, "variable": "nope"})
    assert r.status_code == 404


def test_open_water_soil_wetness_is_422(server, monkeypatch):
    loader = server.api.power_loader

    def raise_no_land(lat, lon, variable):
        raise ValueError(loader.NO_LAND)

    monkeypatch.setattr(loader, "load_point_series", raise_no_land)
    r = TestClient(server.app).get("/api/point", params={"lat": 43, "lon": 34, "variable": "power_soil_wetness"})
    assert r.status_code == 422
    assert "only measured over land" in r.json()["detail"]  # the page turns this into a Turkish message


def test_power_outage_is_502(server, monkeypatch):
    loader = server.api.power_loader

    def raise_power(lat, lon, variable):
        raise loader.PowerError("NASA POWER did not answer.")

    monkeypatch.setattr(loader, "load_point_series", raise_power)
    r = TestClient(server.app).get("/api/point", params={"lat": 37, "lon": 32, "variable": "power_temp"})
    assert r.status_code == 502


def test_page_has_area_mode():
    html = (APP_DIR / "index.html").read_text(encoding="utf-8")
    assert 'id="areaBtn"' in html and "/api/point" in html and "/api/box" in html
