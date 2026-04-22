from __future__ import annotations
from .config import GuardConfig
from .result import GuardResult
from .exceptions import (UnsafeSQLError, raise_blocked_error)
from .engine import parser, extractor, validator, rewriter, suggester


class QueryGuard:

    def __init__(self, config: GuardConfig) -> None:
        self.config = config

    # ── main ────────────────────────────────────────────────────────────────

    def check(self, sql: str, raise_on_blocked: bool = False) -> GuardResult:
        errors: list[str] = []
        warnings: list[str] = []
        detected_tables: list[str] = []

        structure_errors: list[str] = []
        readonly_errors: list[str] = []
        table_errors: list[str] = []
        column_errors: list[str] = []
        star_errors: list[str] = []

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
            # validate SQL structure
            current_structure_errors = validator.validate_sql_structure(ast)
            structure_errors.extend(current_structure_errors)
            errors.extend(current_structure_errors)

            # extract tables
            tables = extractor.extract_tables(ast)
            detected_tables.extend(tables)

            # validate readonly
            current_readonly_errors = validator.validate_readonly(ast, self.config)
            readonly_errors.extend(current_readonly_errors)
            errors.extend(current_readonly_errors)

            # validate table access
            current_table_errors = validator.validate_tables(tables, self.config)
            table_errors.extend(current_table_errors)
            errors.extend(current_table_errors)

            # validate schema columns
            current_column_errors = validator.validate_columns(ast, self.config)
            column_errors.extend(current_column_errors)
            errors.extend(current_column_errors)

            # validate select star
            current_star_errors = validator.validate_select_star(ast, self.config)
            star_errors.extend(current_star_errors)
            errors.extend(current_star_errors)

        detected_tables = list(dict.fromkeys(detected_tables))

        # suggestions for unknown tables
        hints = suggester.suggest(detected_tables, self.config)

        # rewrite only if allowed
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
            raise_blocked_error(
                structure_errors=structure_errors,
                readonly_errors=readonly_errors,
                table_errors=table_errors,
                column_errors=column_errors,
                star_errors=star_errors,
                errors=errors,
            )

        return result

    # ── convenience ─────────────────────────────────────────────────────────

    def check_many(self, sqls: list[str]) -> list[GuardResult]:
        return [self.check(sql) for sql in sqls]

    def is_safe(self, sql: str) -> bool:
        return self.check(sql).allowed

    def rewrite(self, sql: str) -> str:
        result = self.check(sql, raise_on_blocked=True)
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

