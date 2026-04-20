from __future__ import annotations
from sqlglot import exp
from .types import READONLY_TYPES
from ..config import GuardConfig
from ..dialects import get_sqlglot_dialect


def rewrite(ast: exp.Expression, config: GuardConfig) -> str:
    dialect = get_sqlglot_dialect(config.database_type)

    if not isinstance(ast, READONLY_TYPES) or config.max_rows is None:
        return ast.sql(dialect=dialect)

    current_limit = ast.args.get("limit")

    if current_limit is None:
        ast = ast.limit(config.max_rows)
    else:
        limit_expr = current_limit.args.get("expression")

        if not isinstance(limit_expr, exp.Literal):
            ast = ast.limit(config.max_rows)
        else:
            try:
                if int(limit_expr.name) > config.max_rows:
                    ast = ast.limit(config.max_rows)
            except (ValueError, TypeError):
                ast = ast.limit(config.max_rows)

    return ast.sql(dialect=dialect)
