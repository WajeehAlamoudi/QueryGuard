from __future__ import annotations
from sqlglot import exp
from .types import READONLY_TYPES, WRITE_TYPES
from ..config import GuardConfig


def validate_readonly(ast: exp.Expression, config: GuardConfig) -> list[str]:
    if not config.read_only:
        return []

    # if isinstance(ast, WRITE_TYPES):
    #     stmt = type(ast).__name__.upper()
    #     return [f"{stmt} is not allowed in read_only mode"]

    if not isinstance(ast, READONLY_TYPES):
        stmt = type(ast).__name__.upper()
        return [f"{stmt} is not allowed in read_only mode"]

    return []


def validate_tables(tables: list[str], config: GuardConfig) -> list[str]:
    errors: list[str] = []

    allowed_tables = config.allowed_tables

    if allowed_tables is None and config.schema is not None:
        allowed_tables = list(config.schema.keys())

    for table in tables:
        if table in config.blocked_tables:
            errors.append(f"Table '{table}' is blocked")
        elif allowed_tables is not None and table not in allowed_tables:
            errors.append(f"Table '{table}' is not in known tables")

    return errors


def validate_columns(ast: exp.Expression, config: GuardConfig) -> list[str]:
    if config.schema is None:
        return []

    errors: list[str] = []

    aliases: dict[str, str] = {}
    for table in ast.find_all(exp.Table):
        if not table.name:
            continue

        parts: list[str] = []

        if table.catalog:
            parts.append(table.catalog)

        if table.db:
            parts.append(table.db)

        parts.append(table.name)

        full_name = ".".join(part.lower() for part in parts)
        base_name = table.name.lower()

        aliases[base_name] = full_name
        aliases[full_name] = full_name

        alias = table.alias
        if alias:
            aliases[alias.lower()] = full_name

    for column in ast.find_all(exp.Column):
        column_name = column.name.lower() if column.name else ""
        table_ref = column.table.lower() if column.table else ""

        if not column_name:
            continue

        if table_ref:
            table_name = aliases.get(table_ref, table_ref)
            allowed_columns = config.schema.get(table_name)

            if allowed_columns is None:
                continue

            if column_name not in allowed_columns:
                errors.append(
                    f"Column '{column_name}' is not in schema for table '{table_name}'"
                )

            continue

        if len(config.schema) == 1:
            table_name = next(iter(config.schema))
            allowed_columns = config.schema[table_name]

            if column_name not in allowed_columns:
                errors.append(
                    f"Column '{column_name}' is not in schema for table '{table_name}'"
                )

            continue

        matching_tables = [
            table
            for table, columns in config.schema.items()
            if column_name in columns
        ]

        if not matching_tables:
            errors.append(f"Column '{column_name}' is not found in schema")

    return errors


def validate_select_star(ast: exp.Expression, config: GuardConfig) -> list[str]:
    if config.allow_select_star:
        return []

    errors: list[str] = []

    for select in ast.find_all(exp.Select):
        for expression in select.expressions:
            if isinstance(expression, exp.Star):
                errors.append("SELECT * is not allowed")
                continue

            if isinstance(expression, exp.Column) and isinstance(expression.this, exp.Star):
                errors.append("SELECT * is not allowed")

    return errors


def validate_sql_structure(ast: exp.Expression) -> list[str]:
    errors: list[str] = []

    for select in ast.find_all(exp.Select):
        if not select.expressions:
            errors.append("SELECT query must include at least one expression")
            continue

        from_clause = select.args.get("from_")

        for expression in select.expressions:
            is_star = False
            if isinstance(expression, exp.Star):
                is_star = True
            if isinstance(expression, exp.Column) and isinstance(expression.this, exp.Star):
                is_star = True

            if is_star and from_clause is None:
                errors.append("""SELECT * requires a FROM clause""")

    for insert in ast.find_all(exp.Insert):
        if insert.this is None:
            errors.append("INSERT query must include a target table")

    for update in ast.find_all(exp.Update):
        if update.this is None:
            errors.append("UPDATE query must include a target table")

    for delete in ast.find_all(exp.Delete):
        if delete.this is None:
            errors.append("DELETE query must include a target table")

    for limit in ast.find_all(exp.Limit):
        limit_expr = limit.args.get("expression")

        if limit_expr is None:
            errors.append("LIMIT must include a value")
            continue

        if not isinstance(limit_expr, exp.Literal):
            continue

        try:
            value = int(limit_expr.name)
        except (TypeError, ValueError):
            errors.append("LIMIT must be a positive integer")
            continue

        if value <= 0:
            errors.append("LIMIT must be a positive integer")

    return errors
