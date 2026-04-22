from __future__ import annotations


def raise_blocked_error(*, structure_errors: list[str], readonly_errors: list[str], table_errors: list[str], column_errors: list[str], star_errors: list[str], errors: list[str]) -> None:
    if structure_errors:
        raise InvalidSQLStructureError(structure_errors[0])

    if readonly_errors:
        raise ReadOnlyViolation(readonly_errors[0])

    if table_errors:
        first = table_errors[0]
        if "blocked" in first:
            raise BlockedTableError(first)
        raise TableNotAllowedError(first)

    if column_errors:
        raise SchemaValidationError(column_errors[0])

    if star_errors:
        raise SchemaValidationError(star_errors[0])

    raise UnsafeSQLError(errors[0] if errors else "Query blocked")


class QueryGuardError(Exception):
    """Base exception for all QueryGuard errors."""


class UnsupportedDialectError(QueryGuardError):
    """Raised when an unsupported database_type is passed to GuardConfig."""


class UnsafeSQLError(QueryGuardError):
    """Raised when SQL cannot be parsed or is structurally unsafe."""


class ReadOnlyViolation(QueryGuardError):
    """Raised when a write operation is attempted in read_only mode."""


class BlockedTableError(QueryGuardError):
    """Raised when a query references a table in blocked_tables."""


class TableNotAllowedError(QueryGuardError):
    """Raised when a query references a table not in allowed_tables."""


class MaxRowsError(QueryGuardError):
    """Raised when max_rows rewriting fails or produces invalid SQL."""


class InvalidSQLStructureError(UnsafeSQLError):
    """Raised when SQL parses but has invalid or incomplete structure."""


class SchemaValidationError(QueryGuardError):
    """Raised when a query references columns outside the configured schema."""
