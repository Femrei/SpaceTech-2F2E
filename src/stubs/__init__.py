"""TEMP STUBS — stand-ins for teammates' modules until the real ones land on main.

app.py imports ``src.<module>`` first and falls back to ``src.stubs.<module>``
only when the real module does not exist yet, so nothing here ever shadows
real code. Once A, B and D have merged their modules, delete this package.

The interfaces below are an *assumed* contract (the shared spec sections
5 / 6.1-6.4 / 9 were not available when this was written). If a real module
uses different names, align app.py / charts.py with the real one, not this.

  src.data_loader  (A)   DATA_DOWNLOADED_ON: str
                         load_all() -> DataFrame[date, region_id, variable_id, value]
                         load_series(region_id, variable_id) -> Series (freq "MS")
                         available_pairs() -> list[(region_id, variable_id)]

  src.trend        (B)   analyze_trend(series) -> dict with keys:
                           anomalies, trend_line            (Series, original index)
                           slope_per_decade, ci_low, ci_high (OLS, unit / decade)
                           ols_p, mk_p, significant, direction
                           sen_slope_per_decade, percent_change_per_decade
                           mean_value, n_years, start_year, end_year,
                           years_needed_estimate             (None if significant)
                         interpret(result, variable, region) -> str
                         compare_trends(result_a, result_b, region_a, region_b)
                           -> dict(same_direction, both_significant, summary)

  src.detective    (D)   load_catalog(), get_variable(id), get_region(id),
                         THEMES, suggest(theme), glossary(), get_cases(),
                         next_step_hint(result, variable_id, region_id)
"""
