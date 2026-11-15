"""Tests for the detective agent's any-place tool (analyze_place, owner: C).

The chat can answer for places outside the three regions ("Gaziantep'te toprak ne
durumda?") with NASA POWER data around the place. NASA POWER is replaced here by
a synthetic series, so the tests run offline. No LLM is called.

Run from the repo root:  python -m pytest -q
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
APP_DIR = ROOT / "detective3d"


# Sunucu modülünü dosyasından yükler (detective3d bir paket değil).
@pytest.fixture(scope="module")
def server():
    spec = importlib.util.spec_from_file_location("agent_server_place", APP_DIR / "agent_server.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# 1981–2025 aylık yapay seri: mevsim döngüsü + on yılda 1 birimlik azalma.
def _fake_series() -> pd.Series:
    index = pd.date_range("1981-01-01", "2025-12-01", freq="MS")
    t = np.arange(len(index))
    return pd.Series(40 + 15 * np.sin(2 * np.pi * t / 12) - t / 120, index=index)


# NASA POWER kutu isteğini yapay seriyle değiştirir; istenen kutuları da kaydeder.
@pytest.fixture()
def fake_power(server, monkeypatch):
    calls = []

    def load_box(south, west, north, east, variable):
        calls.append((south, west, north, east, variable))
        return {"series": _fake_series(), "n_cells": 4, "cells": [[south + 0.25, west + 0.3]] * 4,
                "area": {"south": south, "west": west, "north": north, "east": east}}

    monkeypatch.setattr(server.api.power_loader, "load_box_series", load_box)
    return calls


def test_city_lookup_handles_turkish_letters_and_suffixes(server):
    assert server.find_city("gaziantep")["name"] == "Gaziantep"
    assert server.find_city("SANLIURFA")["name"] == "Şanlıurfa"
    assert server.find_city("izmir")["name"] == "İzmir"
    assert server.city_in_text("Gaziantepte toprak ne durumda?")["name"] == "Gaziantep"
    assert server.city_in_text("Şanlıurfa'da yağış azalıyor mu?")["name"] == "Şanlıurfa"
    assert server.city_in_text("toprak ne durumda?") is None


def test_analyze_place_uses_city_list(server, fake_power):
    out = server.tool_analyze_place("Gaziantep", "soil_moisture", lat=0, lon=0)  # list wins over model coords
    city = server.find_city("Gaziantep")
    assert out["centre"] == {"lat": round(city["lat"], 4), "lon": round(city["lon"], 4)}
    south, west, north, east, variable = fake_power[0]
    assert south < city["lat"] < north and west < city["lon"] < east
    assert variable == "power_soil_wetness"
    assert out["trend_1981_2025"]["direction"] == "decreasing"
    assert out["trend_1981_2025"]["significant_at_0_05"] is True
    assert out["trend_2001_2025"]["period"] == "2001–2025"
    assert out["what_it_means"]["key"] == "decreasing"
    assert out["map_area"]["label"] == "Gaziantep"


def test_analyze_place_falls_back_to_given_coordinates(server, fake_power):
    out = server.tool_analyze_place("Nizip", "precip", lat=37.01, lon=37.79)
    assert out["located_by"].startswith("coordinates given")
    assert out["percent_change_per_decade"] is not None  # only precipitation gets a % change
    with pytest.raises(ValueError):
        server.tool_analyze_place("Nizip", "precip")  # unknown place and no coordinates


def test_tool_call_moves_the_map(server, fake_power):
    steps, actions, sources = [], [], []
    text = server._run_tool("analyze_place", {"place": "Gaziantep", "variable": "temp", "lat": 37.06, "lon": 37.38},
                            steps, actions, sources)
    assert json.loads(text)["place"] == "Gaziantep"
    assert actions == [{"area": json.loads(text)["map_area"], "variable": "temp"}]
    assert steps[0].startswith("Konum analizi")
    assert sources[0]["dataset"].startswith("NASA POWER")
    # a clue-chain call for another variable must not move the map again
    server._run_tool("analyze_place", {"place": "Gaziantep", "variable": "precip", "lat": 37.06, "lon": 37.38},
                     steps, actions, sources)
    assert len(actions) == 1 and actions[0]["variable"] == "temp"


def test_tool_is_offered_to_the_model(server):
    names = [t["name"] for t in server.TOOLS]
    assert "analyze_place" in names and "analyze_place" in server.HANDLERS
    assert "analyze_place" in server.SYSTEM


def test_offline_chat_answers_for_a_city(server, fake_power):
    out = server.run_offline("Gaziantepte toprak ne durumda?", {})
    assert "Gaziantep" in out["text"] and "yüzey toprak ıslaklığı" in out["text"]
    assert {c[4] for c in fake_power} == {"power_soil_wetness", "power_precip", "power_temp"}  # clue chain
    assert out["actions"][0]["area"]["label"] == "Gaziantep"


def test_offline_chat_still_uses_regions_first(server):
    out = server.run_offline("Konya toprak nemi kuruyor mu?", {})
    assert out["actions"][0]["region"] == "konya"
