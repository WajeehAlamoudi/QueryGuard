from __future__ import annotations
from sqlglot import exp


def extract_tables(ast: exp.Expression) -> list[str]:

    cte_names: set[str] = set()

    for cte in ast.find_all(exp.CTE):
        alias = cte.alias
        if alias:
            cte_names.add(alias.lower())

    tables: list[str] = []
    seen: set[str] = set()

    for table in ast.find_all(exp.Table):

        parts: list[str] = []

        if table.catalog:
            parts.append(table.catalog)

        if table.db:
            parts.append(table.db)

        if table.name:
            parts.append(table.name)

        if not parts:
            continue

        name = ".".join(part.lower() for part in parts)

        if not table.name:
            continue

        base_name = table.name.lower() if table.name else ""

        if name in cte_names or base_name in cte_names:
            continue

        if name in seen:
            continue

        seen.add(name)
        tables.append(name)

    return tables
