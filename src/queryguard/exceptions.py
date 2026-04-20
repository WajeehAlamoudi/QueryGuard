from __future__ import annotations


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
