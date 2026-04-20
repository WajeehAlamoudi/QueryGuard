from __future__ import annotations
from .config import GuardConfig
from .result import GuardResult
from .exceptions import (
    ReadOnlyViolation,
    BlockedTableError,
    TableNotAllowedError,
    UnsafeSQLError,
)
from .engine import parser, extractor, validator, rewriter, suggester


class QueryGuard:

    def __init__(self, config: GuardConfig) -> None:
        self.config = config

    # ── main ────────────────────────────────────────────────────────────────

    def check(self, sql: str, raise_on_blocked: bool = False) -> GuardResult:
        errors: list[str] = []
        warnings: list[str] = []
        detected_tables: list[str] = []

        # 1. parse
        try:
            asts = parser.parse(sql, self.config.database_type)
        except UnsafeSQLError as e:
            result = GuardResult(
                allowed=False,
                original_sql=sql,
                database_type=self.config.database_type,
                errors=[str(e)],
            )
            if raise_on_blocked:
                raise
            return result

        for ast in asts:

            # validate the SQL
            structure_errors = validator.validate_sql_structure(ast)
            errors.extend(structure_errors)

            # 2. extract tables
            tables = extractor.extract_tables(ast)
            detected_tables.extend(tables)

            # 3. validate readonly
            readonly_errors = validator.validate_readonly(ast, self.config)
            errors.extend(readonly_errors)

            # 4. validate table access
            table_errors = validator.validate_tables(tables, self.config)
            errors.extend(table_errors)

            # validate schema columns
            column_errors = validator.validate_columns(ast, self.config)
            errors.extend(column_errors)

            # validate select star
            star_errors = validator.validate_select_star(ast, self.config)
            errors.extend(star_errors)

        detected_tables = list(dict.fromkeys(detected_tables))
        # 5. suggestions for unknown tables
        hints = suggester.suggest(detected_tables, self.config)

        # 6. rewrite only if allowed
        allowed = len(errors) == 0
        final_sql: str | None = None

        if allowed:
            final_sql = "; ".join(
                rewriter.rewrite(ast, self.config)
                for ast in asts
            )

        result = GuardResult(
            allowed=allowed,
            original_sql=sql,
            final_sql=final_sql,
            database_type=self.config.database_type,
            detected_tables=detected_tables,
            errors=errors,
            warnings=warnings,
            suggestions=hints,
        )

        if raise_on_blocked and not allowed:
            first_error = errors[0] if errors else "Query blocked"

            if "read_only mode" in first_error:
                raise ReadOnlyViolation(first_error)
            if "blocked" in first_error:
                raise BlockedTableError(first_error)
            raise TableNotAllowedError(first_error)

        return result

    # ── convenience ─────────────────────────────────────────────────────────

    def check_many(self, sqls: list[str]) -> list[GuardResult]:
        return [self.check(sql) for sql in sqls]

    def is_safe(self, sql: str) -> bool:
        return self.check(sql).allowed

    def rewrite(self, sql: str) -> str:
        result = self.check(sql)
        if not result.allowed:
            raise ValueError("; ".join(result.errors))
        return result.final_sql or sql

    def tables(self, sql: str) -> list[str]:
        asts = parser.parse(sql, self.config.database_type)

        tables: list[str] = []
        for ast in asts:
            tables.extend(extractor.extract_tables(ast))

        return list(dict.fromkeys(tables))

    def explain(self, sql: str) -> str:
        result = self.check(sql)
        lines = []
        for e in result.errors:
            lines.append(f"Blocked: {e}")
        for w in result.warnings:
            lines.append(f"Warning: {w}")
        for table, matches in result.suggestions.items():
            lines.append(f"Suggestion: '{table}' not found — did you mean: {', '.join(matches)}?")
        if not lines:
            lines.append("Allowed: Query passed all policies.")
        return "\n".join(lines)

    def validate(self, sql: str) -> str:
        result = self.check(sql)
        if not result.allowed:
            raise ValueError("; ".join(result.errors) if result.errors else "Query blocked")
        if result.final_sql is None:
            raise ValueError("Query was allowed but no final SQL was produced")
        return result.final_sql

    def set_policy(self, config: GuardConfig) -> None:
        if not isinstance(config, GuardConfig):
            raise TypeError("config must be a GuardConfig")
        self.config = config

