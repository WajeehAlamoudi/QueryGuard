from __future__ import annotations

from typing import Literal

DatabaseType = Literal[
    "mysql",
    "mariadb",
    "postgres",
    "postgresql",
    "sqlite",
    "bigquery",
    "snowflake",
    "duckdb",
    "redshift",
    "trino",
    "presto",
    "spark",
    "tsql",
    "sqlserver",
    "mssql",
    "oracle",
    "clickhouse",
]


DIALECT_MAP: dict[str, str] = {
    "mysql": "mysql",
    "mariadb": "mysql",

    "postgres": "postgres",
    "postgresql": "postgres",

    "sqlite": "sqlite",

    "bigquery": "bigquery",
    "snowflake": "snowflake",
    "duckdb": "duckdb",
    "redshift": "redshift",

    "trino": "trino",
    "presto": "presto",

    "spark": "spark",

    "tsql": "tsql",
    "sqlserver": "tsql",
    "mssql": "tsql",

    "oracle": "oracle",
    "clickhouse": "clickhouse",
}


SUPPORTED_DIALECTS: set[str] = set(DIALECT_MAP)


def get_sqlglot_dialect(database_type: str) -> str:
    return DIALECT_MAP[database_type]
