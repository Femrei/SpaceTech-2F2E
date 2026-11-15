# Data sources

All raw files were downloaded manually from NASA Giovanni (https://giovanni.gsfc.nasa.gov/) on **2026-11-14**
as *Time Series, Area-Averaged*, monthly, starting 2001-01-01.

| Variable | Giovanni dataset | Raw unit | Converted to |
|---|---|---|---|
| precip | GPM_3IMERGM v07 `precipitation` (Final Run) | mm/hr | mm/month (× 24 × days in month) |
| soil_moisture | GLDAS_NOAH025_M v2.1 `SoilMoi0_10cm_inst` | kg/m² | kg/m² (no conversion) |
| temp | M2TMNXSLV (MERRA-2) `T2M` | K | °C (− 273.15) |

Note: IMERG Final Run monthly data were available only up to 2025-09 at download time, so precip is NaN for 2025-10 … 2025-12.

Note on water inside the boxes (measured with `python scripts/check_bbox_water.py`, Natural Earth 10m land and lake
polygons): about **14.5% of the `black_sea` box lies over the Black Sea** (its north edge, 41.2°N, is past the coast in
the western half of the box, where the sea starts near 40.9°N) and about **14% of the `van` box is Lake Van**; the
`konya` box is 99.5% land. Giovanni's area average uses every grid cell with data, so the precipitation (IMERG) and
temperature (MERRA-2) series of those two boxes include water cells; GLDAS soil moisture is land-only. The boxes were
not changed: narrowing them means downloading all series again, so trends there should be read as box averages,
not as land-only values.

| File | Bounding box (W,S,E,N) | Data until | Reproduce URL |
|---|---|---|---|
| `black_sea__precip.csv` | 39.5,40.4,41.6,41.2 | 2025-09-30 | [link](https://giovanni.gsfc.nasa.gov/giovanni/#service=ArAvTs&starttime=2001-01-01T00:00:00Z&endtime=2025-09-30T23:59:59Z&bbox=39.5,40.4,41.6,41.2&data=GPM_3IMERGM_07_precipitation&portal=GIOVANNI&format=json) |
| `black_sea__soil_moisture.csv` | 39.5,40.4,41.6,41.2 | 2025-12-31 | [link](https://giovanni.gsfc.nasa.gov/giovanni/#service=ArAvTs&starttime=2001-01-01T00:00:00Z&endtime=2025-12-31T23:59:59Z&bbox=39.5,40.4,41.6,41.2&data=GLDAS_NOAH025_M_2_1_SoilMoi0_10cm_inst&portal=GIOVANNI&format=json) |
| `black_sea__temp.csv` | 39.5,40.4,41.6,41.2 | 2025-12-31 | [link](https://giovanni.gsfc.nasa.gov/giovanni/#service=ArAvTs&starttime=2001-01-01T00:00:00Z&endtime=2025-12-31T23:59:59Z&bbox=39.5,40.4,41.6,41.2&data=M2TMNXSLV_5_12_4_T2M&portal=GIOVANNI&format=json) |
| `konya__precip.csv` | 32,37.2,34,38.6 | 2025-09-30 | [link](https://giovanni.gsfc.nasa.gov/giovanni/#service=ArAvTs&starttime=2001-01-01T00:00:00Z&endtime=2025-09-30T23:59:59Z&bbox=32,37.2,34,38.6&data=GPM_3IMERGM_07_precipitation&portal=GIOVANNI&format=json) |
| `konya__soil_moisture.csv` | 32,37.2,34,38.6 | 2025-12-31 | [link](https://giovanni.gsfc.nasa.gov/giovanni/#service=ArAvTs&starttime=2001-01-01T00:00:00Z&endtime=2025-12-31T23:59:59Z&bbox=32,37.2,34,38.6&data=GLDAS_NOAH025_M_2_1_SoilMoi0_10cm_inst&portal=GIOVANNI&format=json) |
| `konya__temp.csv` | 32,37.2,34,38.6 | 2025-12-31 | [link](https://giovanni.gsfc.nasa.gov/giovanni/#service=ArAvTs&starttime=2001-01-01T00:00:00Z&endtime=2025-12-31T23:59:59Z&bbox=32,37.2,34,38.6&data=M2TMNXSLV_5_12_4_T2M&portal=GIOVANNI&format=json) |
| `van__precip.csv` | 42,38,44,39.3 | 2025-09-30 | [link](https://giovanni.gsfc.nasa.gov/giovanni/#service=ArAvTs&starttime=2001-01-01T00:00:00Z&endtime=2025-09-30T23:59:59Z&bbox=42,38,44,39.3&data=GPM_3IMERGM_07_precipitation&portal=GIOVANNI&format=json) |
| `van__soil_moisture.csv` | 42,38,44,39.3 | 2025-12-31 | [link](https://giovanni.gsfc.nasa.gov/giovanni/#service=ArAvTs&starttime=2001-01-01T00:00:00Z&endtime=2025-12-31T23:59:59Z&bbox=42,38,44,39.3&data=GLDAS_NOAH025_M_2_1_SoilMoi0_10cm_inst&portal=GIOVANNI&format=json) |
| `van__temp.csv` | 42,38,44,39.3 | 2025-12-31 | [link](https://giovanni.gsfc.nasa.gov/giovanni/#service=ArAvTs&starttime=2001-01-01T00:00:00Z&endtime=2025-12-31T23:59:59Z&bbox=42,38,44,39.3&data=M2TMNXSLV_5_12_4_T2M&portal=GIOVANNI&format=json) |
