from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass(slots=True)
class GuardResult:
    allowed: bool
    original_sql: str
    final_sql: Optional[str] = None
    database_type: Optional[str] = None

    detected_tables: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    suggestions: dict[str, list[str]] = field(default_factory=dict)

    def __repr__(self) -> str:
        status = "ALLOWED" if self.allowed else "BLOCKED"
        return (
            f"GuardResult({status} | "
            f"tables={self.detected_tables} | "
            f"errors={self.errors} | "
            f"suggestions={self.suggestions})"
        )
