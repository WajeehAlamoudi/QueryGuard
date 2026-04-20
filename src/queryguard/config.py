from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Literal, cast
from .exceptions import UnsupportedDialectError
from .dialects import DatabaseType, SUPPORTED_DIALECTS


@dataclass(slots=True)
class GuardConfig:

    # ── database ────────────────────────────────────────
    database_type: DatabaseType

    # ── table access control ─────────────────────────────
    allowed_tables: Optional[list[str]] = None                # None = allow all
    blocked_tables: list[str] = field(default_factory=list)

    # ── write protection ─────────────────────────────────
    read_only: bool = True

    # ── select star ─────────────────────────────────
    allow_select_star: bool = False

    # ── row safety ───────────────────────────────────────
    max_rows: Optional[int] = 1000                            # None = no limit injected

    # ── schema awareness ─────────────────────────────────
    schema: Optional[dict[str, list[str]]] = None

    # ── smart suggestions ────────────────────────────────
    suggest_tables: bool = True
    auto_fix_tables: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.database_type, str):
            raise TypeError("database_type must be a string")

        self.database_type = cast(
            DatabaseType,
            self.database_type.lower().strip()
        )

        if self.database_type not in SUPPORTED_DIALECTS:
            raise UnsupportedDialectError(
                f"Unsupported database_type '{self.database_type}'. "
                f"Choose from: {sorted(SUPPORTED_DIALECTS)}"
            )

        if self.allowed_tables is not None:
            if not isinstance(self.allowed_tables, list):
                raise TypeError("allowed_tables must be a list[str] or None")

            normalized_allowed = []
            for table in self.allowed_tables:
                if not isinstance(table, str):
                    raise TypeError("Each value in allowed_tables must be a string")
                table = table.lower().strip()
                if not table:
                    raise ValueError("allowed_tables cannot contain empty table names")
                normalized_allowed.append(table)

            self.allowed_tables = normalized_allowed

        if not isinstance(self.blocked_tables, list):
            raise TypeError("blocked_tables must be a list[str]")

        normalized_blocked = []
        for table in self.blocked_tables:
            if not isinstance(table, str):
                raise TypeError("Each value in blocked_tables must be a string")
            table = table.lower().strip()
            if not table:
                raise ValueError("blocked_tables cannot contain empty table names")
            normalized_blocked.append(table)

        self.blocked_tables = normalized_blocked

        if not isinstance(self.read_only, bool):
            raise TypeError("read_only must be a bool")

        if not isinstance(self.allow_select_star, bool):
            raise TypeError("allow_select_star must be a bool")

        if self.max_rows is not None:
            if not isinstance(self.max_rows, int) or isinstance(self.max_rows, bool):
                raise TypeError("max_rows must be a positive int or None")
            if self.max_rows <= 0:
                raise ValueError("max_rows must be greater than 0")

        if self.schema is not None:
            if not isinstance(self.schema, dict):
                raise TypeError("schema must be dict[str, list[str]] or None")

            normalized_schema: dict[str, list[str]] = {}
            for table, columns in self.schema.items():
                if not isinstance(table, str):
                    raise TypeError("Each schema key must be a string table name")
                if not isinstance(columns, list):
                    raise TypeError("Each schema value must be a list[str]")

                normalized_table = table.lower().strip()
                if not normalized_table:
                    raise ValueError("schema cannot contain empty table names")

                normalized_columns = []
                for col in columns:
                    if not isinstance(col, str):
                        raise TypeError("Each schema column name must be a string")
                    col = col.lower().strip()
                    if not col:
                        raise ValueError("schema cannot contain empty column names")
                    normalized_columns.append(col)

                normalized_schema[normalized_table] = normalized_columns

            self.schema = normalized_schema

        if not isinstance(self.suggest_tables, bool):
            raise TypeError("suggest_tables must be a bool")

        if not isinstance(self.auto_fix_tables, bool):
            raise TypeError("auto_fix_tables must be a bool")

        if self.auto_fix_tables:
            self.suggest_tables = True
