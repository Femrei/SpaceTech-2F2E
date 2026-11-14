"""TEMP STUBS — stand-ins for teammates' modules until the real ones land on main.

api.py imports ``src.<module>`` first and falls back to ``src.stubs.<module>``
only when the real module does not exist yet, so nothing here ever shadows
real code. A (data_loader) and B (trend) have landed, so only D's stub is left;
delete this package once D's module is merged.

Assumed interface for D (the shared spec section 6.4 was not available when this
was written; if D's real module differs, align api.py with D's, not with this):

  src.detective    (D)   load_catalog() -> {variables, regions, glossary, cases}
                         get_variable(id), get_region(id)   (KeyError if unknown)
                         THEMES: {key: question}
                         suggest(theme) -> [{variable_id, region_id, reason}]  (best first)
                         glossary() -> {term: definition}
                         get_cases() -> [{id, title, story, region_id, variable_id,
                                          compare_region_id}]
                         next_step_hint(result, variable_id, region_id) -> str
"""
