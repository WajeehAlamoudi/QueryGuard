from __future__ import annotations

from typing import Optional

from .dialects import DatabaseType


class GuardConfig:
    database_type: DatabaseType
    allowed_tables: Optional[list[str]]
    blocked_tables: list[str]
    read_only: bool
    allow_select_star: bool
    max_rows: Optional[int]
    schema: Optional[dict[str, list[str]]]
    suggest_tables: bool
    auto_fix_tables: bool

    def __init__(
        self,
        database_type: DatabaseType,
        allowed_tables: Optional[list[str]] = None,
        blocked_tables: list[str] = ...,
        read_only: bool = True,
        allow_select_star: bool = False,
        max_rows: Optional[int] = 1000,
        schema: Optional[dict[str, list[str]]] = None,
        suggest_tables: bool = True,
        auto_fix_tables: bool = False,
    ) -> None: ...
