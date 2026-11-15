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
import re
import shutil
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
    for name in ("index.html", "data.js", "power_data.js", "cities.js"):
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


def test_data_js_carries_hint_box_context():
    """The hint box reads the catalog's context texts (English and Turkish) from data.js."""
    text = (APP_DIR / "data.js").read_text(encoding="utf-8")
    data = json.loads(text[text.index("=") + 1:].strip().rstrip(";"))
    for variable in data["variables"]:
        assert {"context", "context_tr"} <= set(variable), variable["id"]


def test_page_has_no_projection_case_or_ndvi_window():
    """The team chose not to show 2035/2050 projections, a "what could be done" list, case files
    or the MODIS NDVI farm windows (the green squares). The GIBS NDVI imagery layer stays."""
    html = (APP_DIR / "index.html").read_text(encoding="utf-8")
    for needle in ("p2035", "p2050", "outlookOf", "olActs", "caseBtn", "goCase",
                   "ndvi_data.js", "NDVI_DATA", "ndvi-sites", "ndviHTML"):
        assert needle not in html, needle
    assert 'id="tourToggle"' in html and 'id="ndviToggle"' in html


def test_page_script_parses(tmp_path):
    """A broken edit in index.html leaves a blank page; node --check catches it (skipped without Node.js)."""
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is not installed")
    html = (APP_DIR / "index.html").read_text(encoding="utf-8")
    script = tmp_path / "page.js"
    script.write_text("\n".join(re.findall(r"<script>(.*?)</script>", html, re.S)), encoding="utf-8")
    result = subprocess.run([node, "--check", str(script)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_agent_has_no_ndvi_window_tool(server):
    assert "get_ndvi_trend" not in server.HANDLERS
    assert all(tool["name"] != "get_ndvi_trend" for tool in server.TOOLS)
    with pytest.raises(server.HTTPException):
        server.static_file("ndvi_data.js")
    out = server.run_offline("Konya'da bitki örtüsü yeşilleniyor mu?", {})
    assert "NDVI" not in out["text"]



def test_data_js_carries_decision_card_inputs():
    """The decision card, the Sen interval tile and the "next clue" button read these from data.js."""
    text = (APP_DIR / "data.js").read_text(encoding="utf-8")
    data = json.loads(text[text.index("=") + 1:].strip().rstrip(";"))
    for variable in data["variables"]:
        assert variable["short_description_tr"]
    for key, pair in data["pairs"].items():
        res = pair["result"]
        assert {"sen_ci_low", "sen_ci_high", "years_needed_estimate", "n_years", "start_year", "end_year"} <= set(res), key
        assert res["sen_ci_low"] <= res["sen_slope_per_decade"] <= res["sen_ci_high"], key
        # the rough "years of data needed" estimate exists exactly when the trend is not significant
        assert (res["years_needed_estimate"] is None) == bool(res["significant"]) or res["sen_slope_per_decade"] == 0, key
        assert {"text", "text_tr", "variable_id", "region_id"} <= set(pair["next_step"]), key


def test_page_has_decision_card_and_chart():
    html = (APP_DIR / "index.html").read_text(encoding="utf-8")
    for needle in ("function verdictHTML", "function hintBoxHTML", "function nextStepHTML", "function yearsNeededHTML",
                   'id="chartBack"', "function renderChart"):
        assert needle in html, needle
    assert "sen_ci_low" in html and "olsCi95" in html      # the interval is labelled by the slope it belongs to
    for key in ("vdWhat", "ynWeak", "ynNote", "chartBig", "viewAnom", "nextBtn", "tour"):  # both languages
        assert html.count(f"{key}:") == 2, key


def test_page_has_yearly_stripes_and_heat_window():
    """The left panel shows yearly stripes; "Enlarge" opens a window with a years and a year x month view."""
    html = (APP_DIR / "index.html").read_text(encoding="utf-8")
    for needle in ("function anomalyGrid", "function stripesSVG", "function heatPanelHTML", "function renderHeat",
                   'id="heatBack"', 'id="heatOpen"', 'data-hv="years"', 'data-hv="months"'):
        assert needle in html, needle
    assert "heatmapSVG" not in html
    for key in ("stripesTitle", "heatBig", "viewYears", "viewMonths", "yearRead", "monthRead", "heatNoteY", "heatNoteM"):
        assert html.count(f"{key}:") == 2, key  # Turkish and English
