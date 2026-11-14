"""Earth Trend Detective: Streamlit entry point (owner: C).

Run with:  streamlit run app.py
"""
from __future__ import annotations

import importlib

import streamlit as st

from src.charts import time_series_chart

st.set_page_config(layout="wide", page_title="Earth Trend Detective", page_icon="🛰️")
# Let metric values wrap instead of being cut off with "…" on narrow screens.
st.markdown(
    "<style>[data-testid='stMetricValue'] > div {white-space: normal; "
    "overflow: visible; font-size: 1.6rem; line-height: 1.25;}</style>",
    unsafe_allow_html=True,
)


# --------------------------------------------------------------------------- #
# Module wiring: use teammates' real modules when present, else TEMP stubs.
# --------------------------------------------------------------------------- #
# Takım arkadaşının modülünü yükler (ör. src.trend).
# Gerçek modül henüz yoksa src/stubs altındaki geçici sürümü kullanır.
# İkinci dönen değer True ise stub kullanılıyor demektir.
def _load_module(name: str):
    try:
        return importlib.import_module(f"src.{name}"), False
    except ModuleNotFoundError as err:
        if err.name != f"src.{name}":  # the real module exists but is broken: surface it
            raise
        return importlib.import_module(f"src.stubs.{name}"), True


data_loader, _stub_a = _load_module("data_loader")   # A
trend, _stub_b = _load_module("trend")               # B
detective, _stub_d = _load_module("detective")       # D
STUBS_IN_USE = [n for n, s in [("data_loader (A)", _stub_a), ("trend (B)", _stub_b),
                                ("detective (D)", _stub_d)] if s]


# --------------------------------------------------------------------------- #
# Cached data access
# --------------------------------------------------------------------------- #
# Seçilen bölge + değişken için aylık zaman serisini getirir.
# @st.cache_data sayesinde aynı seçim için veri tekrar tekrar okunmaz.
@st.cache_data(show_spinner=False)
def get_series(region_id: str, variable_id: str):
    return data_loader.load_series(region_id, variable_id)


# Seriyi B'nin analyze_trend fonksiyonuna verip trend sonucunu (dict) döndürür.
# Sonuç önbellekte tutulur; aynı seçimde istatistik yeniden hesaplanmaz.
@st.cache_data(show_spinner=False)
def get_result(region_id: str, variable_id: str):
    return trend.analyze_trend(get_series(region_id, variable_id))


# Verisi bulunan (bölge, değişken) çiftlerini küme olarak döndürür.
# Explore'da seçilen kombinasyonun verisi var mı diye kontrol etmek için kullanılır.
@st.cache_data(show_spinner=False)
def get_pairs() -> set[tuple[str, str]]:
    return set(data_loader.available_pairs())


# D'nin sözlüğünden (glossary) bir terimin açıklamasını bulur.
# Metrik kutularındaki (?) ipuçlarında help= olarak gösterilir. Bulamazsa None döner.
def term_help(term: str) -> str | None:
    """Glossary definition for a term (case-insensitive), used as a tooltip."""
    gloss = detective.glossary()
    lookup = {k.lower(): v for k, v in gloss.items()}
    return lookup.get(term.lower())


# --------------------------------------------------------------------------- #
# Result card
# --------------------------------------------------------------------------- #
# Sonuç kartını çizer:
#   1) 3 metrik kutusu: 10 yıllık değişim, % değişim, anlamlılık (+ p-değeri)
#   2) B'nin interpret() fonksiyonundan gelen açıklama metni
#   3) Açılır 'Statistical details' bölümü: OLS eğimi + güven aralığı,
#      Mann-Kendall p, Sen eğimi, yıl sayısı
def render_result_card(result: dict, variable: dict, region: dict) -> None:
    unit = variable["unit"]
    pct = result.get("percent_change_per_decade")

    c1, c2, c3 = st.columns(3)
    c1.metric("Change per decade", f"{result['slope_per_decade']:+.2f} {unit}",
              help=term_help("per decade"))
    c2.metric("% per decade", f"{pct:+.1f}%" if pct is not None else "n/a",
              help="Change per decade relative to the long-term average.")
    c3.metric("Significance",
              "✅ Significant" if result["significant"] else "⚪ Not significant",
              help=term_help("statistically significant"))
    c3.caption(f"Mann-Kendall p = {result['mk_p']:.3f}")

    st.markdown(f"> {trend.interpret(result, variable, region)}")

    with st.expander("📊 Statistical details"):
        d1, d2, d3, d4 = st.columns(4)
        d1.metric("OLS slope", f"{result['slope_per_decade']:+.3f} {unit}/decade",
                  help=term_help("trend"))
        d1.caption(f"95% CI: {result['ci_low']:+.3f} to {result['ci_high']:+.3f}")
        d2.metric("Mann-Kendall p-value", f"{result['mk_p']:.4f}",
                  help=term_help("Mann-Kendall test") or term_help("p-value"))
        d3.metric("Sen's slope", f"{result['sen_slope_per_decade']:+.3f} {unit}/decade",
                  help=term_help("Sen's slope"))
        d4.metric("Years of data", result["n_years"], help=term_help("area-averaged"))
        st.caption(
            "The trend is fitted to monthly **anomalies** (each month minus its long-term "
            "average for that calendar month), so the seasonal cycle does not create a fake trend. "
            f"Confidence interval: {term_help('confidence interval') or ''}"
        )


# --------------------------------------------------------------------------- #
# Tabs
# --------------------------------------------------------------------------- #
# Explore sekmesinin tamamı:
# bölge/değişken seçimi -> değişken açıklaması -> grafik -> sonuç kartı.
# Veri yoksa ya da yetersizse (24 aydan az) kullanıcıya uyarı gösterir.
def render_explore() -> None:
    catalog = detective.load_catalog()
    regions = [r["id"] for r in catalog["regions"]]
    variables = [v["id"] for v in catalog["variables"]]

    c1, c2 = st.columns(2)
    region_id = c1.selectbox("Region", regions, key="explore_region",
                             format_func=lambda i: detective.get_region(i)["name"])
    variable_id = c2.selectbox("Variable", variables, key="explore_variable",
                               format_func=lambda i: detective.get_variable(i)["name"])
    region = detective.get_region(region_id)
    variable = detective.get_variable(variable_id)

    st.caption(f"**{variable['name']}:** {variable['short_description']}")

    if (region_id, variable_id) not in get_pairs():
        st.warning(f"No data available yet for {variable['name']} in {region['name']}.")
        return

    try:
        with st.spinner("Analysing the trend…"):
            series = get_series(region_id, variable_id)
            result = get_result(region_id, variable_id)
    except ValueError as err:
        st.warning(f"Not enough data to analyse this series. {err}")
        return

    st.plotly_chart(time_series_chart(series, result, variable, region),
                    width="stretch")
    st.caption(f"Source dataset: {variable['dataset']} · {variable['unit']} · area-averaged "
               f"over the {region['name']}")
    render_result_card(result, variable, region)


# Henüz yapılmamış sekmeler için 'yakında' bilgi kutusu gösterir.
def render_coming_soon(what: str) -> None:
    st.info(f"🚧 {what} is coming soon. Use **🧭 Explore** for now.")


# --------------------------------------------------------------------------- #
# Page
# --------------------------------------------------------------------------- #
# Sayfanın ana akışı: başlık -> (stub uyarısı) -> 4 sekme -> altbilgi (veri kaynağı).
st.title("🛰️ Earth Trend Detective")
st.markdown("Become a data detective: find out what's changing on Earth, where, how fast, "
            "and whether it's significant.")

if STUBS_IN_USE:
    st.sidebar.warning("Development build: using placeholder modules for "
                       + ", ".join(STUBS_IN_USE) + ". Numbers are mock data.")

tab_detective, tab_explore, tab_cases, tab_compare = st.tabs(
    ["🔍 Detective Mode", "🧭 Explore", "📁 Case Files", "⚖️ Compare"])
with tab_detective:
    render_coming_soon("Detective Mode")
with tab_explore:
    render_explore()
with tab_cases:
    render_coming_soon("Case Files")
with tab_compare:
    render_coming_soon("Compare")

# Altbilgi: her sekmede görünür; veri setleri ve indirme tarihi yazılır.
st.divider()
datasets = " · ".join(v["dataset"] for v in detective.load_catalog()["variables"])
st.caption(f"Datasets: {datasets}. "
           f"Data: NASA Giovanni, pre-downloaded on {data_loader.DATA_DOWNLOADED_ON}")
