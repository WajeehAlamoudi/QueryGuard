from __future__ import annotations
import sqlglot
from typing import cast
from sqlglot import exp
from ..exceptions import UnsafeSQLError
from ..dialects import get_sqlglot_dialect


def parse(sql: str, database_type: str) -> list[exp.Expression]:
    dialect = get_sqlglot_dialect(database_type)
    cleaned_sql = sql.strip()

    if not cleaned_sql:
        raise UnsafeSQLError("SQL is empty")

    try:
        statements = sqlglot.parse(cleaned_sql, read=dialect)
    except sqlglot.errors.ParseError as e:
        raise UnsafeSQLError(f"Failed to parse SQL: {e}") from e

    if not statements:
        raise UnsafeSQLError("SQL parsed to empty result")

    parsed: list[exp.Expression] = []

    for statement in statements:
        if statement is None:
            raise UnsafeSQLError("SQL parsed to empty statement")
        parsed.append(cast(exp.Expression, statement))

    return parsed
