"""
İşlenmiş veriyi okuma katmanı. B ve C bu modüle güveniyor: imzaları değiştirme.

Kullanım:
    from src.data_loader import load_series, available_pairs
    s = load_series("konya", "temp")   # 300 elemanlı, freq='MS', °C
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

DATA_PATH = Path(__file__).resolve().parent.parent / "data/processed/all_series.csv"

# TODO(A): Giovanni'den gerçek indirme tarihini yaz (YYYY-MM-DD).
DATA_DOWNLOADED_ON = "2026-11-14"


@lru_cache(maxsize=1)
def load_all() -> pd.DataFrame:
    """Tüm tabloyu döndürür: date (datetime), region_id, variable_id, value.

    Önbellekli olduğu için dönen DataFrame'i yerinde değiştirme; gerekiyorsa .copy() al.
    """
    df = pd.read_csv(DATA_PATH, parse_dates=["date"])
    return df


def load_series(region_id: str, variable_id: str) -> pd.Series:
    """Bir bölge-değişken çifti için tam aylık (freq='MS') seri döndürür."""
    df = load_all()
    sub = df[(df["region_id"] == region_id) & (df["variable_id"] == variable_id)]
    if sub.empty:
        raise KeyError(f"Veri yok: ({region_id!r}, {variable_id!r}). "
                       f"Mevcut çiftler: {available_pairs()}")
    s = sub.set_index("date")["value"].sort_index().asfreq("MS")
    s.name = f"{region_id}__{variable_id}"
    return s


def available_pairs() -> list[tuple[str, str]]:
    """Veride bulunan (region_id, variable_id) çiftleri, sıralı."""
    df = load_all()
    pairs = df[["region_id", "variable_id"]].drop_duplicates()
    return sorted(map(tuple, pairs.to_numpy()))
