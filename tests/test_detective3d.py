"""Smoke tests for the 3D app server (detective3d/agent_server.py, owner D).

They make sure the app still works on top of the repo's modules (A's data,
B's trend.py, C's api.py, D's detective.py). No LLM is called: the tools and the
offline chat are plain Python.

Run from the repo root:  python -m pytest -q
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
APP_DIR = ROOT / "detective3d"
REGIONS = ("konya", "van", "black_sea")
VARIABLES = ("precip", "soil_moisture", "temp")


@pytest.fixture(scope="module")
def server():
    spec = importlib.util.spec_from_file_location("agent_server", APP_DIR / "agent_server.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_app_files_exist():
    for name in ("index.html", "data.js", "power_data.js", "ndvi_data.js", "cities.js"):
        assert (APP_DIR / name).is_file(), name


def test_server_finds_repo_root(server):
    assert server.REPO == ROOT


def test_data_js_has_all_pairs():
    text = (APP_DIR / "data.js").read_text(encoding="utf-8")
    data = json.loads(text[text.index("=") + 1:].strip().rstrip(";"))
    pairs = set(data["pairs"])
    assert {f"{r}|{v}" for r in REGIONS for v in VARIABLES} <= pairs


@pytest.mark.parametrize("region", REGIONS)
@pytest.mark.parametrize("variable", VARIABLES)
def test_get_trend_tool(server, region, variable):
    out = server.tool_get_trend(region, variable)
    assert out["direction"] in ("increasing", "decreasing", "no change")
    assert out["what_it_means"]["key"] in ("increasing", "decreasing", "no_clear_trend")
    assert out["what_it_means"]["text"]


def test_other_tools(server):
    assert len(server.tool_get_overview()) == 9
    assert server.tool_compare_regions("soil_moisture", "konya", "black_sea")
    assert server.tool_get_long_record("konya", "temp")["series"]


def test_offline_chat_answers_with_real_numbers(server):
    out = server.run_offline("Konya toprak nemi kuruyor mu?", {})
    assert out["offline"] is True
    assert "Konya" in out["text"] and "kg/m²" in out["text"]
    assert out["actions"][0]["region"] == "konya"


def test_static_files_are_allowlisted(server):
    with pytest.raises(server.HTTPException):
        server.static_file("agent_server.py")  # source code must not be served


def test_server_starts_with_non_utf8_output():
    """Windows regression: with stdout redirected to a cp1254 pipe the start-up print crashed."""
    env = {**os.environ, "PYTHONIOENCODING": "cp1254", "PORT": "0", "HOST": "127.0.0.1"}
    env.pop("PYTHONUTF8", None)
    proc = subprocess.Popen([sys.executable, str(APP_DIR / "agent_server.py")], cwd=ROOT, env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        output = b""
        deadline = time.time() + 60
        while time.time() < deadline and b"startup complete" not in output:
            line = proc.stdout.readline()
            if not line:  # process exited
                break
            output += line
    finally:
        proc.kill()
        proc.wait()
    text = output.decode("utf-8", errors="replace")
    assert "UnicodeEncodeError" not in text, text
    assert "startup complete" in text, text



@pytest.mark.parametrize(("text", "city"), [
    # a city name followed by nothing, an apostrophe or a Turkish case suffix is a city
    ("Gaziantepte toprak ne durumda?", "Gaziantep"),
    ("Gaziantep'te toprak ne durumda?", "Gaziantep"),
    ("Sanliurfada yagis", "Şanlıurfa"),
    ("Kars'ı göster", "Kars"),
    ("Kars ne durumda", "Kars"),
    ("Muş'ta sıcaklık", "Muş"),
    ("Erzurum'daki kar", "Erzurum"),
    ("İzmir'in yağışı", "İzmir"),
    # ordinary words that only start like a city are not (offline mode used to analyse Kars / Muş)
    ("Toprak nemini karşılaştır", None),
    ("İki bölgeyi karşılaştır lütfen", None),
    ("musluk suyu azaldı mı", None),
    ("toprak ne durumda?", None),
])
def test_city_in_text_needs_a_whole_name(server, text, city):
    found = server.city_in_text(text)
    assert (found["name"] if found else None) == city
