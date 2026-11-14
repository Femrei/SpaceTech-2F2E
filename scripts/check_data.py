"""
Veri kalitesi raporu: data/processed/all_series.csv mantıklı mı?

Kontroller (her seri için):
  1. NaN oranı ve en uzun ardışık eksik dönem
  2. Birim makul mü (fiziksel aralık + birim dönüşümü unutulmuş mu?)
  3. Mevsimsellik doğru mu (ör. Temmuz > Ocak; Konya Temmuz ort. 20–30 °C)
  4. Aykırı değerler (anomali z-skoru > 4)
  5. Ani kopuş / seviye sıçraması (önceki ve sonraki 3 yılın ortalaması çok farklı mı)

Kullanım:
    python scripts/check_data.py
Çıkış kodu: hata varsa 1, sadece uyarı varsa veya her şey yolundaysa 0.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.data_loader import available_pairs, load_series  # noqa: E402

# Değişken başına fiziksel olarak makul aylık alan ortalaması aralıkları
RANGES = {
    "precip": (0.0, 1000.0),         # mm/month
    "soil_moisture": (1.0, 50.0),    # kg/m², 0–10 cm katman (≈ %1–50 hacimsel nem)
    "temp": (-40.0, 45.0),           # °C
}
UNITS = {"precip": "mm/month", "soil_moisture": "kg/m²", "temp": "°C"}

MAX_NAN_RATIO = 0.05      # %5'ten fazla eksik → uyarı
MAX_NAN_RUN = 6           # 6 aydan uzun kesintisiz boşluk → uyarı
OUTLIER_Z = 4.0
BREAK_WINDOW = 36         # ay
BREAK_THRESHOLD = 1.5     # pencere ortalamaları farkı / anomali std


def longest_nan_run(s: pd.Series) -> int:
    isna = s.isna().to_numpy()
    best = run = 0
    for v in isna:
        run = run + 1 if v else 0
        best = max(best, run)
    return best


def check_units(s: pd.Series, var: str) -> list[tuple[str, str]]:
    """(seviye, mesaj) listesi döndürür. seviye: 'HATA' veya 'UYARI'."""
    out = []
    v = s.dropna()
    lo, hi = RANGES[var]

    # Tipik birim hatalarını önce, açık bir mesajla yakala
    if var == "temp" and v.mean() > 150:
        return [("HATA", f"ortalama {v.mean():.1f} → hâlâ Kelvin gibi (−273.15 unutulmuş)")]
    if var == "precip":
        annual = v.groupby(v.index.year).sum().mean()
        if annual < 20:
            return [("HATA", f"yıllık toplam ≈ {annual:.2f} mm → mm/hr veya mm/day "
                             f"→ mm/month dönüşümü yapılmamış olabilir")]
        if annual > 5000:
            return [("HATA", f"yıllık toplam ≈ {annual:.0f} mm → dönüşüm iki kez yapılmış olabilir")]

    n_out = int(((v < lo) | (v > hi)).sum())
    if n_out:
        out.append(("HATA", f"{n_out} değer makul aralığın [{lo}, {hi}] {UNITS[var]} dışında"))
    if var == "precip" and (v < 0).any():
        out.append(("HATA", "negatif yağış var"))
    return out


def check_seasonality(s: pd.Series, var: str, region: str) -> list[tuple[str, str]]:
    out = []
    clim = s.groupby(s.index.month).mean()
    if var == "temp":
        if not clim[7] > clim[1]:
            out.append(("HATA", f"Temmuz ({clim[7]:.1f}) Ocak'tan ({clim[1]:.1f}) sıcak değil"))
        if region == "konya" and not 20 <= clim[7] <= 30:
            out.append(("UYARI", f"Konya Temmuz ortalaması {clim[7]:.1f} °C (beklenen 20–30)"))
    if var == "precip" and region == "konya" and clim[7] > clim[1]:
        # İç Anadolu'da yazlar kurak, kış/ilkbahar yağışlı
        out.append(("UYARI", f"Konya'da Temmuz yağışı ({clim[7]:.1f}) Ocak'tan "
                             f"({clim[1]:.1f}) fazla, beklenmedik"))
    return out


def anomalies(s: pd.Series) -> pd.Series:
    return s - s.groupby(s.index.month).transform("mean")


def check_outliers(s: pd.Series) -> list[tuple[str, str]]:
    a = anomalies(s)
    z = (a - a.mean()) / a.std()
    bad = z[z.abs() > OUTLIER_Z]
    if bad.empty:
        return []
    months = ", ".join(f"{d:%Y-%m} (z={v:+.1f})" for d, v in bad.items())
    return [("UYARI", f"aykırı aylar: {months}")]


def check_breaks(s: pd.Series) -> list[tuple[str, str]]:
    a = anomalies(s)
    std = a.std()
    if not std or np.isnan(std):
        return []
    before = a.rolling(BREAK_WINDOW, min_periods=BREAK_WINDOW // 2).mean()
    after = a[::-1].rolling(BREAK_WINDOW, min_periods=BREAK_WINDOW // 2).mean()[::-1]
    diff = (after.shift(-1) - before).abs() / std
    if diff.max() > BREAK_THRESHOLD:
        when = diff.idxmax()
        return [("UYARI", f"{when:%Y-%m} civarında olası seviye kopuşu "
                          f"(fark = {diff.max():.1f} std) — grafiğe bak")]
    return []


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    pairs = available_pairs()
    print(f"{len(pairs)} seri kontrol ediliyor (beklenen 9)\n")
    rows, n_err, n_warn = [], 0, 0

    for region, var in pairs:
        s = load_series(region, var)
        nan_ratio = s.isna().mean()
        nan_run = longest_nan_run(s)
        issues = []
        if nan_ratio > MAX_NAN_RATIO:
            issues.append(("UYARI", f"NaN oranı %{nan_ratio * 100:.1f}"))
        if nan_run > MAX_NAN_RUN:
            issues.append(("UYARI", f"{nan_run} ay kesintisiz eksik"))
        if s.notna().sum() < 24:
            issues.append(("HATA", "24'ten az geçerli değer, trend analizi yapılamaz"))
        else:
            issues += check_units(s, var)
            issues += check_seasonality(s, var, region)
            issues += check_outliers(s)
            issues += check_breaks(s)

        n_err += sum(1 for lvl, _ in issues if lvl == "HATA")
        n_warn += sum(1 for lvl, _ in issues if lvl == "UYARI")
        status = "❌" if any(l == "HATA" for l, _ in issues) else ("⚠️" if issues else "✅")
        jul = s[s.index.month == 7].mean()
        rows.append({"seri": f"{region}/{var}", "durum": status, "n": len(s),
                     "NaN%": round(nan_ratio * 100, 1), "min": round(s.min(), 2),
                     "ort": round(s.mean(), 2), "max": round(s.max(), 2),
                     "Temmuz ort": round(jul, 2), "birim": UNITS[var]})
        for lvl, msg in issues:
            print(f"  {status} {region}/{var} [{lvl}] {msg}")

    if len(pairs) != 9:
        print(f"  ❌ 9 seri bekleniyordu, {len(pairs)} bulundu [HATA]")
        n_err += 1

    print("\n" + pd.DataFrame(rows).to_string(index=False))
    print(f"\nSonuç: {n_err} hata, {n_warn} uyarı")
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main())
