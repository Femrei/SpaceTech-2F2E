"""Tests for the TR/EN language switch of the 3D app (owner: C).

The page sends ui_state.lang ("tr" or "en"); the server answers the offline chat,
the step labels and its error messages in that language. No LLM is called.

Run from the repo root:  python -m pytest -q
"""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
APP_DIR = ROOT / "detective3d"
TURKISH_LETTERS = re.compile("[çğıöşüÇĞİÖŞÜ]")


# Sunucu modülünü dosyasından yükler (detective3d bir paket değil).
@pytest.fixture(scope="module")
def server():
    spec = importlib.util.spec_from_file_location("agent_server_lang", APP_DIR / "agent_server.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_language_is_read_from_ui_state(server):
    assert server._lang({"lang": "en"}) == "en"
    assert server._lang({"lang": "tr"}) == "tr"
    assert server._lang({}) == "tr" and server._lang(None) == "tr"


def test_step_labels_follow_the_language(server):
    args = {"region": "black_sea", "variable": "soil_moisture"}
    assert server._step_label("get_trend", args, "en") == "Trend analysis: Eastern Black Sea · soil moisture"
    assert server._step_label("get_trend", args, "tr") == "Trend analizi: Doğu Karadeniz · toprak nemi"
    assert server._step_label("control_map", {"region": "van"}, "en").startswith("Map")  # the page marks map steps


def test_offline_answer_in_english(server):
    out = server.run_offline("Is the soil drying in Konya?", {"lang": "en"})
    text = out["text"]
    assert "Konya" in text and "per decade" in text and "Offline mode" in text
    assert not TURKISH_LETTERS.search(text.split("Clue (catalog):")[0])  # no Turkish before the English catalog hint
    assert all(not TURKISH_LETTERS.search(s) for s in out["steps"])


def test_offline_answer_stays_turkish_by_default(server):
    out = server.run_offline("Konya'da toprak kuruyor mu?", {})
    assert "on yılda" in out["text"] and "Çevrimdışı mod" in out["text"]


def test_empty_message_error_in_english(server):
    r = TestClient(server.app).post("/api/chat", json={"message": "  ", "ui_state": {"lang": "en"}})
    assert r.status_code == 400 and r.json()["detail"] == "Empty message."


def test_system_prompt_asks_for_the_page_language(server):
    assert "lang in the map note" in server.SYSTEM
    assert "lang=en" in server._map_note({"lang": "en"})


def test_page_has_both_languages():
    html = (APP_DIR / "index.html").read_text(encoding="utf-8")
    assert 'data-lang="tr"' in html and 'data-lang="en"' in html
    assert 'data-guide="tr"' in html and 'data-guide="en"' in html
    for key in ("pageTitle", "welcome", "areaWarn", "story"):  # same keys in both dictionaries
        assert html.count(f"{key}:") >= 2, key
