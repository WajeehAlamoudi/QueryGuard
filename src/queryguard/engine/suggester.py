from __future__ import annotations
from ..config import GuardConfig
from ..utils.similarity import find_similar


def suggest(tables: list[str], config: GuardConfig) -> dict[str, list[str]]:
    if not config.suggest_tables:
        return {}

    if config.allowed_tables is not None:
        known = config.allowed_tables
    elif config.schema is not None:
        known = list(config.schema.keys())
    else:
        known = []

    if not known:
        return {}

    suggestions: dict[str, list[str]] = {}

    for table in tables:
        if table in known:
            continue

        matches = find_similar(table, known)

        if not matches:
            base_table = table.split(".")[-1]
            matches = find_similar(base_table, known)

        if matches:
            suggestions[table] = matches

    return suggestions

