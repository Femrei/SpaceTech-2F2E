"""Repo'yu salt-okunur kullanarak prototip için data.js üretir.

Repo dosyalarına dokunmaz; api.py içindeki fonksiyonları doğrudan çağırır
(B'nin trend analizi, D'nin kataloğu). Bytecode da yazılmaz.
Kullanım (repo kökünden):  python detective3d/build_data.py
"""
import json
import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
repo = Path(sys.argv[1] if len(sys.argv) > 1 else HERE.parent).resolve()
sys.path.insert(0, str(repo))
os.chdir(repo)
import api  # noqa: E402

import re  # noqa: E402

# Provenance: dataset per variable and the exact Giovanni request per region × variable,
# both read from A's data/SOURCES.md.
src_md = (repo / "data" / "SOURCES.md").read_text(encoding="utf-8")
DATASETS = {m.group(1): m.group(2).strip() for m in re.finditer(r"^\| (\w+) \| ([^|]+?) \|", src_md, re.M)
            if m.group(1) not in ("Variable",)}
LINKS = {f"{m.group(1)}|{m.group(2)}": m.group(3)
         for m in re.finditer(r"`(\w+?)__(\w+)\.csv` \|[^\n]*?\[link\]\((\S+?)\)", src_md)}

meta = api.meta()
out = {
    "regions": meta["regions"],
    "variables": meta["variables"],
    "no_percent_variables": meta["no_percent_variables"],
    "data_downloaded_on": meta.get("data_downloaded_on"),
    "pairs": {},
}
for region, variable in meta["pairs"]:
    a = api.analysis(region, variable)
    out["pairs"][f"{region}|{variable}"] = {
        "points": [{k: p[k] for k in ("date", "value", "smooth", "anomaly")} for p in a["points"]],
        "result": {k: a["result"].get(k) for k in (
            "sen_slope_per_decade", "percent_change_per_decade", "significant",
            "direction", "mk_p", "mean_value", "ci_low", "ci_high", "slope_per_decade",
            # decision card: Sen slope's own interval, record length and the rough
            # "years of data needed" estimate (None when the trend is significant)
            "sen_ci_low", "sen_ci_high", "years_needed_estimate", "n_years", "start_year", "end_year")},
        "interpretation": a["interpretation"],
        # D's catalog clue (text, text_tr and the variable/region it points to) for the panel button
        "next_step": a["next_step"],
        "source": {"dataset": DATASETS.get(variable), "url": LINKS.get(f"{region}|{variable}"),
                   "via": "NASA Giovanni, area-averaged time series"},
    }

# data.js: index.html çift tıklanıp (file://) açılınca da çalışsın diye
# veri JSON yerine bir <script> olarak yüklenir.
dest = HERE / "data.js"
dest.write_text("window.TREND_DATA = " + json.dumps(out, ensure_ascii=False) + ";\n", encoding="utf-8")
print("written:", dest, len(out["pairs"]), "pairs")
