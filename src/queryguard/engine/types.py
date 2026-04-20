from __future__ import annotations
from sqlglot import exp


WRITE_TYPES = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Create,
    exp.Alter,
    exp.TruncateTable,
    exp.Merge,
)
READONLY_TYPES = (
    exp.Select,
    exp.Union,
    exp.Intersect,
    exp.Except,
)
