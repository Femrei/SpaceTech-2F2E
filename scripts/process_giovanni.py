"""
Giovanni ham CSV'lerini tek bir uzun formatlı tabloya dönüştürür.

Girdi : data/raw/<region_id>__<variable_id>.csv   (9 dosya)
Çıktı : data/processed/all_series.csv
        sütunlar: date,region_id,variable_id,value
        her seri 2001-01-01 → 2025-12-01 arası tam 300 satır

Kullanım:
    python scripts/process_giovanni.py
"""

from __future__ import annotations

import calendar
import csv
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Ayarlar
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
OUT_PATH = ROOT / "data" / "processed" / "all_series.csv"

START = "2001-01-01"
END = "2025-12-01"
EXPECTED_MONTHS = 300

CATALOG_PATH = ROOT / "data" / "catalog.json"   # D'nin dosyası, sadece okunur

# Bölüm 5 / D'nin catalog.json'u ile aynı olmalı.
KNOWN_REGIONS = {"konya", "van", "black_sea"}
KNOWN_VARIABLES = {"precip", "soil_moisture", "temp"}

# Giovanni bazen tek bir fill value satırı vermez; bunlar da NaN sayılır.
GENERIC_FILL_VALUES = [-9999.0, -9999.9, -999.0, -99999.0, 1e15, 1e20, -1e15]

# Değişken başına kabul edilen birimler (Giovanni başlığında geçen yazımlar)
PRECIP_UNITS = {"mm/hr": "mm/hr", "mm/h": "mm/hr", "mm hr-1": "mm/hr",
                "mm/day": "mm/day", "mm/d": "mm/day", "mm day-1": "mm/day",
                "mm/month": "mm/month", "mm month-1": "mm/month"}


# ---------------------------------------------------------------------------
# Ham dosyayı okuma
# ---------------------------------------------------------------------------
def parse_filename(path: Path) -> tuple[str, str]:
    """'konya__temp.csv' -> ('konya', 'temp'). Bilinmeyen ID'de hata verir."""
    stem = path.stem
    if "__" not in stem:
        raise ValueError(f"{path.name}: dosya adı '<region_id>__<variable_id>.csv' olmalı")
    region_id, variable_id = stem.split("__", 1)
    if region_id not in KNOWN_REGIONS:
        raise ValueError(f"{path.name}: bilinmeyen region_id '{region_id}'. "
                         f"Bilinenler: {sorted(KNOWN_REGIONS)}")
    if variable_id not in KNOWN_VARIABLES:
        raise ValueError(f"{path.name}: bilinmeyen variable_id '{variable_id}'. "
                         f"Bilinenler: {sorted(KNOWN_VARIABLES)}")
    return region_id, variable_id


def read_giovanni_csv(path: Path) -> tuple[pd.DataFrame, list[str]]:
    """Metadata satırlarını atlayıp veri tablosunu döndürür.

    Başlık satırı sabit bir satır numarasıyla değil, içeriğine bakılarak bulunur:
    ilk hücresi 'time' (veya 'date') olan satır.
    """
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    header_idx = None
    for i, line in enumerate(lines):
        first_cell = next(csv.reader([line]), [""])
        first_cell = first_cell[0].strip().lower() if first_cell else ""
        if first_cell in ("time", "date"):
            header_idx = i
            break
    if header_idx is None:
        raise ValueError(f"{path.name}: 'time,...' başlık satırı bulunamadı")

    metadata = lines[:header_idx]
    df = pd.read_csv(path, skiprows=header_idx, encoding="utf-8-sig")
    df.columns = [c.strip() for c in df.columns]
    if df.shape[1] < 2:
        raise ValueError(f"{path.name}: veri tablosunda değer sütunu yok")
    df = df.iloc[:, :2]
    df.columns = ["time", "value"]
    return df, metadata


def find_fill_value(metadata: list[str]) -> float | None:
    for line in metadata:
        if line.lower().startswith("fill value"):
            cells = next(csv.reader([line]))
            for cell in reversed(cells):
                try:
                    return float(cell)
                except ValueError:
                    continue
    return None


# Giovanni'nin gerçek CSV başlığında birim YAZMIYOR. Bu yüzden birimi, indirme
# sırasında Giovanni'nin değişken tablosundaki "Units" sütununda gördüğümüz
# değerden alıyoruz. Değişken listesinde başka birim seçersen burayı güncelle.
GIOVANNI_UNITS = {
    "precip": "mm/hr",          # GPM_3IMERGM v07 precipitation (Units: mm/hr)
    "soil_moisture": "kg/m2",   # GLDAS_NOAH025_M v2.1 SoilMoi0_10cm_inst (kg/m^2)
    "temp": "K",                # M2TMNXSLV T2M (K)
}


def detect_unit(metadata: list[str], variable_id: str) -> tuple[str, str]:
    """(birim, kaynak) döndürür. Önce metadata'ya bakar, yoksa GIOVANNI_UNITS'i kullanır."""
    try:
        return _unit_from_metadata(metadata, variable_id), "başlık"
    except ValueError:
        return GIOVANNI_UNITS[variable_id], "GIOVANNI_UNITS"


def _unit_from_metadata(metadata: list[str], variable_id: str) -> str:
    text = " ".join(metadata).lower()
    if variable_id == "precip":
        # uzun eşleşmeler önce (mm/hr, mm/h'den önce gelmeli)
        for raw in sorted(PRECIP_UNITS, key=len, reverse=True):
            if raw in text:
                return PRECIP_UNITS[raw]
    elif variable_id == "temp":
        if re.search(r"\bk\b|kelvin", text):
            return "K"
        if "degc" in text or "°c" in text or "deg c" in text:
            return "C"
    elif variable_id == "soil_moisture":
        if re.search(r"kg[ /]?m(\^?-?2|²)|kg m-2", text):
            return "kg/m2"
    raise ValueError(f"{variable_id}: metadata'da birim bulunamadı. Ham dosyanın "
                     f"başlığına bakıp PRECIP_UNITS/detect_unit'i güncelle.")


# ---------------------------------------------------------------------------
# Temizleme ve dönüştürme
# ---------------------------------------------------------------------------
def clean_values(s: pd.Series, fill_value: float | None) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce")
    fills = list(GENERIC_FILL_VALUES)
    if fill_value is not None:
        fills.append(fill_value)
    for fv in fills:
        s = s.mask(np.isclose(s, fv, rtol=1e-6, atol=1e-6))
    # 1e15 civarı ve üstü her şey fill value'dur
    s = s.mask(s.abs() >= 1e14)
    return s


def convert_units(s: pd.Series, variable_id: str, unit: str) -> pd.Series:
    if variable_id == "precip":
        days = pd.Series([calendar.monthrange(d.year, d.month)[1] for d in s.index],
                         index=s.index)
        if unit == "mm/hr":
            return s * 24 * days
        if unit == "mm/day":
            return s * days
        return s  # zaten mm/month
    if variable_id == "temp":
        return s - 273.15 if unit == "K" else s
    return s  # soil_moisture: kg/m², dönüşüm yok


def process_file(path: Path) -> tuple[pd.DataFrame, dict]:
    region_id, variable_id = parse_filename(path)
    df, metadata = read_giovanni_csv(path)
    unit, unit_source = detect_unit(metadata, variable_id)
    fill_value = find_fill_value(metadata)

    dates = pd.to_datetime(df["time"].astype(str).str.strip(), errors="coerce")
    bad_dates = int(dates.isna().sum())
    df = df.assign(date=dates.dt.to_period("M").dt.to_timestamp())  # ayın 1'i
    df = df.dropna(subset=["date"])

    values = clean_values(df["value"], fill_value)
    s = pd.Series(values.to_numpy(), index=pd.DatetimeIndex(df["date"]), name="value")

    if s.index.duplicated().any():
        raise ValueError(f"{path.name}: aynı ay birden fazla kez var")

    full_index = pd.date_range(START, END, freq="MS")
    s = s.reindex(full_index)  # aralığa kırp + eksik ayları NaN ile doldur
    s = convert_units(s, variable_id, unit)

    out = pd.DataFrame({
        "date": full_index.strftime("%Y-%m-%d"),
        "region_id": region_id,
        "variable_id": variable_id,
        "value": s.round(4).to_numpy(),
    })
    info = {"file": path.name, "unit_in": unit, "unit_source": unit_source,
            "fill_value": fill_value,
            "bad_dates": bad_dates}
    return out, info


def _catalog_ids(section) -> set[str]:
    """catalog.json'daki bir bölümden ID'leri çıkarır (liste veya sözlük olabilir)."""
    if isinstance(section, dict):
        return set(section.keys())
    if isinstance(section, list):
        return {item["id"] for item in section if isinstance(item, dict) and "id" in item}
    return set()


def check_catalog_sync() -> None:
    """D'nin catalog.json'u varsa ID'lerin bizimkilerle aynı olduğunu kontrol eder."""
    if not CATALOG_PATH.exists():
        print("(catalog.json henüz yok, ID senkron kontrolü atlandı)")
        return
    import json
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    for name, ours in (("regions", KNOWN_REGIONS), ("variables", KNOWN_VARIABLES)):
        theirs = _catalog_ids(catalog.get(name))
        if theirs and theirs != ours:
            print(f"UYARI: catalog.json '{name}' ID'leri farklı! "
                  f"bizde={sorted(ours)} katalogda={sorted(theirs)} → D ile konuş",
                  file=sys.stderr)
        elif theirs:
            print(f"catalog.json '{name}' ID'leri uyumlu ✓")


# ---------------------------------------------------------------------------
# Ana akış
# ---------------------------------------------------------------------------
def main() -> int:
    # Windows terminallerinde °, ², ✓ gibi karakterler hata vermesin
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    check_catalog_sync()
    files = sorted(RAW_DIR.glob("*.csv"))
    if not files:
        print(f"HATA: {RAW_DIR} içinde CSV yok", file=sys.stderr)
        return 1

    frames, infos = [], []
    for f in files:
        out, info = process_file(f)
        frames.append(out)
        infos.append(info)

    result = pd.concat(frames, ignore_index=True)
    result = result.sort_values(["region_id", "variable_id", "date"]).reset_index(drop=True)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUT_PATH, index=False)

    # ---- Özet ----
    print(f"\n{len(files)} dosya işlendi → {OUT_PATH.relative_to(ROOT)} "
          f"({len(result)} satır)\n")
    print("Algılanan ham birimler (lütfen kontrol et):")
    for info in infos:
        print(f"  {info['file']:<35} birim={info['unit_in']:<7} "
              f"(kaynak: {info['unit_source']:<14}) "
              f"fill={info['fill_value']}  okunamayan tarih={info['bad_dates']}")

    summary = (result.groupby(["region_id", "variable_id"])["value"]
               .agg(rows="size", nan=lambda v: int(v.isna().sum()),
                    min="min", mean="mean", max="max")
               .round(2))
    print("\nSeri özeti (çıktı birimleri: precip=mm/month, "
          "soil_moisture=kg/m², temp=°C):")
    print(summary.to_string())

    problems = summary[summary["rows"] != EXPECTED_MONTHS]
    if not problems.empty:
        print(f"\nUYARI: {EXPECTED_MONTHS} satır olmayan seriler var!", file=sys.stderr)
        return 1
    if len(files) != 9:
        print(f"\nUYARI: 9 dosya bekleniyordu, {len(files)} bulundu.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
