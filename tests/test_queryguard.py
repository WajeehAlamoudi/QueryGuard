import pytest

from queryguard import (
    QueryGuard,
    GuardConfig,
    GuardResult,
    UnsupportedDialectError,
    UnsafeSQLError,
    ReadOnlyViolation,
    BlockedTableError,
    TableNotAllowedError,
)


# ---------------------------------------------------------------------
# GuardConfig
# ---------------------------------------------------------------------


def test_config_normalizes_database_type():
    config = GuardConfig(database_type=" MySQL ")

    assert config.database_type == "mysql"


def test_config_rejects_unsupported_database_type():
    with pytest.raises(UnsupportedDialectError):
        GuardConfig(database_type="mongodb")


def test_config_rejects_non_string_database_type():
    with pytest.raises(TypeError):
        GuardConfig(database_type=123)


def test_config_normalizes_allowed_tables():
    config = GuardConfig(
        database_type="mysql",
        allowed_tables=[" Users ", "ORDERS"],
    )

    assert config.allowed_tables == ["users", "orders"]


def test_config_rejects_non_list_allowed_tables():
    with pytest.raises(TypeError):
        GuardConfig(database_type="mysql", allowed_tables="users")


def test_config_rejects_non_string_allowed_table():
    with pytest.raises(TypeError):
        GuardConfig(database_type="mysql", allowed_tables=["users", 123])


def test_config_rejects_empty_allowed_table():
    with pytest.raises(ValueError):
        GuardConfig(database_type="mysql", allowed_tables=["users", " "])


def test_config_normalizes_blocked_tables():
    config = GuardConfig(
        database_type="mysql",
        blocked_tables=[" Payments ", "ADMIN_USERS"],
    )

    assert config.blocked_tables == ["payments", "admin_users"]


def test_config_rejects_non_list_blocked_tables():
    with pytest.raises(TypeError):
        GuardConfig(database_type="mysql", blocked_tables="payments")


def test_config_rejects_non_string_blocked_table():
    with pytest.raises(TypeError):
        GuardConfig(database_type="mysql", blocked_tables=["payments", 123])


def test_config_rejects_empty_blocked_table():
    with pytest.raises(ValueError):
        GuardConfig(database_type="mysql", blocked_tables=["payments", " "])


def test_config_rejects_non_bool_read_only():
    with pytest.raises(TypeError):
        GuardConfig(database_type="mysql", read_only="yes")


def test_config_accepts_max_rows_none():
    config = GuardConfig(database_type="mysql", max_rows=None)

    assert config.max_rows is None


def test_config_rejects_non_int_max_rows():
    with pytest.raises(TypeError):
        GuardConfig(database_type="mysql", max_rows="100")


def test_config_rejects_bool_max_rows():
    with pytest.raises(TypeError):
        GuardConfig(database_type="mysql", max_rows=True)


def test_config_rejects_zero_max_rows():
    with pytest.raises(ValueError):
        GuardConfig(database_type="mysql", max_rows=0)


def test_config_rejects_negative_max_rows():
    with pytest.raises(ValueError):
        GuardConfig(database_type="mysql", max_rows=-1)


def test_config_normalizes_schema():
    config = GuardConfig(
        database_type="mysql",
        schema={
            " Users ": [" ID ", "NAME"],
            "ORDERS": [" Id ", "USER_ID"],
        },
    )

    assert config.schema == {
        "users": ["id", "name"],
        "orders": ["id", "user_id"],
    }


def test_config_rejects_non_dict_schema():
    with pytest.raises(TypeError):
        GuardConfig(database_type="mysql", schema=["users"])


def test_config_rejects_non_string_schema_table():
    with pytest.raises(TypeError):
        GuardConfig(database_type="mysql", schema={123: ["id"]})


def test_config_rejects_empty_schema_table():
    with pytest.raises(ValueError):
        GuardConfig(database_type="mysql", schema={" ": ["id"]})


def test_config_rejects_non_list_schema_columns():
    with pytest.raises(TypeError):
        GuardConfig(database_type="mysql", schema={"users": "id"})


def test_config_rejects_non_string_schema_column():
    with pytest.raises(TypeError):
        GuardConfig(database_type="mysql", schema={"users": ["id", 123]})


def test_config_rejects_empty_schema_column():
    with pytest.raises(ValueError):
        GuardConfig(database_type="mysql", schema={"users": ["id", " "]})


def test_config_rejects_non_bool_suggest_tables():
    with pytest.raises(TypeError):
        GuardConfig(database_type="mysql", suggest_tables="yes")


def test_config_rejects_non_bool_auto_fix_tables():
    with pytest.raises(TypeError):
        GuardConfig(database_type="mysql", auto_fix_tables="yes")


def test_config_auto_fix_enables_suggestions():
    config = GuardConfig(
        database_type="mysql",
        suggest_tables=False,
        auto_fix_tables=True,
    )

    assert config.suggest_tables is True


# ---------------------------------------------------------------------
# Basic QueryGuard behavior
# ---------------------------------------------------------------------


def test_check_returns_guard_result():
    guard = QueryGuard(GuardConfig(database_type="mysql"))

    result = guard.check("SELECT * FROM users")

    assert isinstance(result, GuardResult)


def test_select_query_is_allowed_by_default():
    guard = QueryGuard(GuardConfig(database_type="mysql"))

    result = guard.check("SELECT id FROM users")

    assert result.allowed is True
    assert result.errors == []


def test_final_sql_contains_limit_by_default():
    guard = QueryGuard(GuardConfig(database_type="mysql"))

    result = guard.check("SELECT id FROM users")

    assert result.final_sql == "SELECT id FROM users LIMIT 1000"


def test_max_rows_none_does_not_add_limit():
    guard = QueryGuard(GuardConfig(database_type="mysql", max_rows=None))

    result = guard.check("SELECT id FROM users")

    assert result.final_sql == "SELECT id FROM users"


def test_existing_safe_limit_is_kept():
    guard = QueryGuard(GuardConfig(database_type="mysql", max_rows=100))

    result = guard.check("SELECT id FROM users LIMIT 50")

    assert result.final_sql == "SELECT id FROM users LIMIT 50"


def test_existing_high_limit_is_lowered():
    guard = QueryGuard(GuardConfig(database_type="mysql", max_rows=100))

    result = guard.check("SELECT id FROM users LIMIT 500")

    assert result.final_sql == "SELECT id FROM users LIMIT 100"


def test_detected_tables_are_returned():
    guard = QueryGuard(GuardConfig(database_type="mysql", max_rows=None))

    result = guard.check(
        "SELECT * FROM users JOIN orders ON users.id = orders.user_id"
    )

    assert set(result.detected_tables) == {"users", "orders"}


def test_tables_helper_returns_detected_tables():
    guard = QueryGuard(GuardConfig(database_type="mysql"))

    tables = guard.tables(
        "SELECT * FROM users JOIN orders ON users.id = orders.user_id"
    )

    assert set(tables) == {"users", "orders"}


def test_check_many_returns_result_for_each_query():
    guard = QueryGuard(GuardConfig(database_type="mysql"))

    results = guard.check_many([
        "SELECT * FROM users",
        "SELECT * FROM orders",
    ])

    assert len(results) == 2
    assert all(isinstance(result, GuardResult) for result in results)


def test_is_safe_returns_true_for_allowed_query():
    guard = QueryGuard(GuardConfig(database_type="mysql"))

    assert guard.is_safe("SELECT id FROM users") is True


def test_is_safe_returns_false_for_blocked_query():
    guard = QueryGuard(
        GuardConfig(database_type="mysql", blocked_tables=["users"])
    )

    assert guard.is_safe("SELECT * FROM users") is False


def test_rewrite_returns_final_sql():
    guard = QueryGuard(GuardConfig(database_type="mysql", max_rows=10))

    sql = guard.rewrite("SELECT id FROM users")

    assert sql == "SELECT id FROM users LIMIT 10"


def test_rewrite_raises_for_blocked_query():
    guard = QueryGuard(
        GuardConfig(database_type="mysql", blocked_tables=["users"])
    )

    with pytest.raises(BlockedTableError):
        guard.rewrite("SELECT id FROM users")


def test_validate_returns_final_sql():
    guard = QueryGuard(GuardConfig(database_type="mysql", max_rows=10))

    sql = guard.validate("SELECT id FROM users")

    assert sql == "SELECT id FROM users LIMIT 10"


def test_validate_raises_for_blocked_query():
    guard = QueryGuard(
        GuardConfig(database_type="mysql", blocked_tables=["users"])
    )

    with pytest.raises(ValueError):
        guard.validate("SELECT * FROM users")


def test_set_policy_replaces_config():
    guard = QueryGuard(
        GuardConfig(database_type="mysql", allowed_tables=["users"])
    )

    guard.set_policy(
        GuardConfig(database_type="mysql", allowed_tables=["orders"])
    )

    assert guard.is_safe("SELECT id FROM users") is False
    assert guard.is_safe("SELECT id FROM orders") is True


# ---------------------------------------------------------------------
# Read-only validation
# ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO users (id) VALUES (1)",
        "UPDATE users SET name = 'Ali' WHERE id = 1",
        "DELETE FROM users WHERE id = 1",
        "DROP TABLE users",
        "CREATE TABLE users (id INT)",
        "ALTER TABLE users ADD COLUMN age INT",
        "TRUNCATE TABLE users",
    ],
)
def test_write_queries_are_blocked_in_read_only_mode(sql):
    guard = QueryGuard(GuardConfig(database_type="mysql", read_only=True))

    result = guard.check(sql)

    assert result.allowed is False
    assert result.errors


def test_write_queries_can_be_allowed_when_read_only_false():
    guard = QueryGuard(
        GuardConfig(database_type="mysql", read_only=False, max_rows=None)
    )

    result = guard.check("DELETE FROM users WHERE id = 1")

    assert result.allowed is True


def test_raise_on_blocked_readonly_raises_specific_exception():
    guard = QueryGuard(GuardConfig(database_type="mysql", read_only=True))

    with pytest.raises(ReadOnlyViolation):
        guard.check("DELETE FROM users", raise_on_blocked=True)


# ---------------------------------------------------------------------
# Table policy validation
# ---------------------------------------------------------------------


def test_allowed_tables_allows_known_table():
    guard = QueryGuard(
        GuardConfig(database_type="mysql", allowed_tables=["users"])
    )

    result = guard.check("SELECT id FROM users")

    assert result.allowed is True


def test_allowed_tables_blocks_unknown_table():
    guard = QueryGuard(
        GuardConfig(database_type="mysql", allowed_tables=["users"])
    )

    result = guard.check("SELECT * FROM orders")

    assert result.allowed is False
    assert "Table 'orders' is not in known tables" in result.errors


def test_blocked_tables_blocks_table():
    guard = QueryGuard(
        GuardConfig(database_type="mysql", blocked_tables=["payments"])
    )

    result = guard.check("SELECT * FROM payments")

    assert result.allowed is False
    assert "Table 'payments' is blocked" in result.errors


def test_blocked_tables_take_priority_over_allowed_tables():
    guard = QueryGuard(
        GuardConfig(
            database_type="mysql",
            allowed_tables=["payments"],
            blocked_tables=["payments"],
        )
    )

    result = guard.check("SELECT * FROM payments")

    assert result.allowed is False
    assert "Table 'payments' is blocked" in result.errors


def test_raise_on_blocked_table_raises_specific_exception():
    guard = QueryGuard(
        GuardConfig(database_type="mysql", blocked_tables=["payments"])
    )

    with pytest.raises(BlockedTableError):
        guard.check("SELECT * FROM payments", raise_on_blocked=True)


def test_raise_on_not_allowed_table_raises_specific_exception():
    guard = QueryGuard(
        GuardConfig(database_type="mysql", allowed_tables=["users"])
    )

    with pytest.raises(TableNotAllowedError):
        guard.check("SELECT * FROM payments", raise_on_blocked=True)


# ---------------------------------------------------------------------
# Suggestions
# ---------------------------------------------------------------------


def test_suggests_similar_allowed_table_name():
    guard = QueryGuard(
        GuardConfig(
            database_type="mysql",
            allowed_tables=["users", "orders"],
            suggest_tables=True,
        )
    )

    result = guard.check("SELECT * FROM usres")

    assert result.allowed is False
    assert result.suggestions == {"usres": ["users"]}


def test_suggestions_can_be_disabled():
    guard = QueryGuard(
        GuardConfig(
            database_type="mysql",
            allowed_tables=["users", "orders"],
            suggest_tables=False,
        )
    )

    result = guard.check("SELECT * FROM usres")

    assert result.suggestions == {}


def test_suggestions_use_schema_when_allowed_tables_is_none():
    guard = QueryGuard(
        GuardConfig(
            database_type="mysql",
            schema={"users": ["id"], "orders": ["id"]},
            suggest_tables=True,
        )
    )

    result = guard.check("SELECT * FROM usres")

    assert result.suggestions == {"usres": ["users"]}


def test_explain_reports_blocked_query():
    guard = QueryGuard(
        GuardConfig(database_type="mysql", blocked_tables=["payments"])
    )

    explanation = guard.explain("SELECT * FROM payments")

    assert "Blocked: Table 'payments' is blocked" in explanation


def test_explain_reports_allowed_query():
    guard = QueryGuard(GuardConfig(database_type="mysql"))

    explanation = guard.explain("SELECT id FROM users")

    assert explanation == "Allowed: Query passed all policies."


# ---------------------------------------------------------------------
# Parser / unsafe SQL
# ---------------------------------------------------------------------


def test_invalid_sql_is_blocked():
    guard = QueryGuard(GuardConfig(database_type="mysql"))

    result = guard.check("SELECT FROM WHERE")

    assert result.allowed is False
    assert result.errors
    assert "Failed to parse SQL" in result.errors[0]


def test_invalid_sql_raises_when_raise_on_blocked_true():
    guard = QueryGuard(GuardConfig(database_type="mysql"))

    with pytest.raises(UnsafeSQLError):
        guard.check("SELECT FROM WHERE", raise_on_blocked=True)


def test_empty_sql_is_blocked():
    guard = QueryGuard(GuardConfig(database_type="mysql"))

    result = guard.check("   ")

    assert result.allowed is False


def test_multi_statement_sql_is_blocked():
    guard = QueryGuard(GuardConfig(database_type="mysql"))

    result = guard.check("SELECT * FROM users; DROP TABLE users")

    assert result.allowed is False


# ---------------------------------------------------------------------
# CTEs, aliases, and nested queries
# ---------------------------------------------------------------------


def test_table_alias_does_not_replace_real_table_name():
    guard = QueryGuard(GuardConfig(database_type="mysql", max_rows=None))

    result = guard.check("SELECT u.id FROM users AS u")

    assert result.allowed is True
    assert result.detected_tables == ["users"]


def test_join_aliases_detect_real_tables():
    guard = QueryGuard(GuardConfig(database_type="mysql", max_rows=None))

    result = guard.check(
        "SELECT u.id, o.id FROM users u JOIN orders o ON u.id = o.user_id"
    )

    assert set(result.detected_tables) == {"users", "orders"}


def test_subquery_detects_inner_table():
    guard = QueryGuard(GuardConfig(database_type="mysql", max_rows=None))

    result = guard.check(
        "SELECT * FROM users WHERE id IN (SELECT user_id FROM orders)"
    )

    assert set(result.detected_tables) == {"users", "orders"}


def test_cte_detects_underlying_table():
    guard = QueryGuard(GuardConfig(database_type="mysql", max_rows=None))

    result = guard.check(
        """
        WITH active_users AS (
            SELECT * FROM users WHERE active = 1
        )
        SELECT * FROM active_users
        """
    )

    assert "users" in result.detected_tables


# ---------------------------------------------------------------------
# Set operations
# ---------------------------------------------------------------------


def test_union_query_is_allowed_in_read_only_mode():
    guard = QueryGuard(GuardConfig(database_type="mysql", max_rows=None))

    result = guard.check(
        "SELECT id FROM users UNION SELECT id FROM orders"
    )

    assert result.allowed is True


def test_union_query_gets_limited_when_max_rows_is_set():
    guard = QueryGuard(GuardConfig(database_type="mysql", max_rows=10))

    result = guard.check(
        "SELECT id FROM users UNION SELECT id FROM orders"
    )

    assert "LIMIT 10" in result.final_sql


def test_intersect_query_is_allowed_in_read_only_mode():
    guard = QueryGuard(GuardConfig(database_type="postgres", max_rows=None))

    result = guard.check(
        "SELECT id FROM users INTERSECT SELECT id FROM orders"
    )

    assert result.allowed is True


def test_except_query_is_allowed_in_read_only_mode():
    guard = QueryGuard(GuardConfig(database_type="postgres", max_rows=None))

    result = guard.check(
        "SELECT id FROM users EXCEPT SELECT id FROM orders"
    )

    assert result.allowed is True


# ---------------------------------------------------------------------
# Dialects
# ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "database_type",
    [
        "mysql",
        "postgres",
        "sqlite",
        "bigquery",
        "snowflake",
        "duckdb",
        "redshift",
        "trino",
        "presto",
        "spark",
        "tsql",
        "oracle",
        "clickhouse",
    ],
)
def test_supported_dialects_can_create_config(database_type):
    config = GuardConfig(database_type=database_type)

    assert config.database_type == database_type


def test_postgres_sql_is_rewritten_with_postgres_dialect():
    guard = QueryGuard(GuardConfig(database_type="postgres", max_rows=10))

    result = guard.check("SELECT id FROM users")

    assert result.final_sql == "SELECT id FROM users LIMIT 10"


def test_tsql_top_query_parses_when_tsql_supported():
    guard = QueryGuard(
        GuardConfig(database_type="tsql", max_rows=10, allow_select_star=True)
    )

    result = guard.check("SELECT TOP 5 * FROM users")

    assert result.allowed is True


def test_multiple_safe_selects_are_allowed():
    guard = QueryGuard(GuardConfig(database_type="mysql", max_rows=10))

    result = guard.check("SELECT id FROM users; SELECT id FROM orders")

    assert result.allowed is True
    assert result.final_sql == "SELECT id FROM users LIMIT 10; SELECT id FROM orders LIMIT 10"
    assert set(result.detected_tables) == {"users", "orders"}


def test_multiple_statements_blocked_if_one_statement_is_unsafe():
    guard = QueryGuard(GuardConfig(database_type="mysql", read_only=True))

    result = guard.check("SELECT * FROM users; DROP TABLE users")

    assert result.allowed is False
    assert result.final_sql is None
    assert result.errors


def test_multiple_statements_blocked_if_one_table_is_not_allowed():
    guard = QueryGuard(
        GuardConfig(database_type="mysql", allowed_tables=["users"])
    )

    result = guard.check("SELECT * FROM users; SELECT * FROM payments")

    assert result.allowed is False
    assert "Table 'payments' is not in known tables" in result.errors



def test_cte_alias_is_not_reported_as_real_table():
    guard = QueryGuard(
        GuardConfig(
            database_type="mysql",
            allowed_tables=["users"],
            max_rows=None,
        )
    )

    result = guard.check(
        """
        WITH active_users AS (
            SELECT * FROM users
        )
        SELECT * FROM active_users
        """
    )

    assert result.allowed is True
    assert result.detected_tables == ["users"]


def test_multiple_cte_aliases_are_not_reported_as_real_tables():
    guard = QueryGuard(
        GuardConfig(
            database_type="mysql",
            allowed_tables=["users", "orders"],
            max_rows=None,
        )
    )

    result = guard.check(
        """
        WITH active_users AS (
            SELECT id FROM users
        ),
        recent_orders AS (
            SELECT id, user_id FROM orders
        )
        SELECT active_users.id, recent_orders.id
        FROM active_users
        JOIN recent_orders ON active_users.id = recent_orders.user_id
        """
    )

    assert result.allowed is True
    assert set(result.detected_tables) == {"users", "orders"}


def test_cte_inner_blocked_table_is_still_detected():
    guard = QueryGuard(
        GuardConfig(
            database_type="mysql",
            blocked_tables=["payments"],
            max_rows=None,
        )
    )

    result = guard.check(
        """
        WITH payment_data AS (
            SELECT * FROM payments
        )
        SELECT * FROM payment_data
        """
    )

    assert result.allowed is False
    assert "Table 'payments' is blocked" in result.errors


def test_schema_qualified_table_is_detected_with_schema():
    guard = QueryGuard(
        GuardConfig(database_type="postgres", max_rows=None)
    )

    result = guard.check("SELECT * FROM analytics.users")

    assert result.detected_tables == ["analytics.users"]


def test_schema_qualified_table_requires_full_allowed_name():
    guard = QueryGuard(
        GuardConfig(
            database_type="postgres",
            allowed_tables=["users"],
            max_rows=None,
        )
    )

    result = guard.check("SELECT * FROM analytics.users")

    assert result.allowed is False
    assert "Table 'analytics.users' is not in known tables" in result.errors


def test_schema_qualified_table_allowed_by_full_name():
    guard = QueryGuard(
        GuardConfig(
            database_type="postgres",
            allowed_tables=["analytics.users"],
            max_rows=None,
        )
    )

    result = guard.check("SELECT id FROM analytics.users")

    assert result.allowed is True
    assert result.detected_tables == ["analytics.users"]


def test_cte_alias_is_not_reported_as_real_table():
    guard = QueryGuard(
        GuardConfig(
            database_type="mysql",
            allowed_tables=["users"],
            max_rows=None,
        )
    )

    result = guard.check(
        """
        WITH active_users AS (
            SELECT id FROM users
        )
        SELECT id FROM active_users
        """
    )

    assert result.allowed is True
    assert result.detected_tables == ["users"]


def test_schema_allows_known_column():
    guard = QueryGuard(
        GuardConfig(
            database_type="mysql",
            schema={"users": ["id", "name"]},
            max_rows=None,
        )
    )

    result = guard.check("SELECT id, name FROM users")

    assert result.allowed is True


def test_schema_blocks_unknown_column():
    guard = QueryGuard(
        GuardConfig(
            database_type="mysql",
            schema={"users": ["id", "name"]},
            max_rows=None,
        )
    )

    result = guard.check("SELECT password FROM users")

    assert result.allowed is False
    assert "Column 'password' is not in schema for table 'users'" in result.errors


def test_schema_blocks_unknown_qualified_column_with_alias():
    guard = QueryGuard(
        GuardConfig(
            database_type="mysql",
            schema={"users": ["id", "name"]},
            max_rows=None,
        )
    )

    result = guard.check("SELECT u.password FROM users u")

    assert result.allowed is False
    assert "Column 'password' is not in schema for table 'users'" in result.errors


def test_schema_allows_join_columns_with_aliases():
    guard = QueryGuard(
        GuardConfig(
            database_type="mysql",
            schema={
                "users": ["id", "name"],
                "orders": ["id", "user_id", "total"],
            },
            max_rows=None,
        )
    )

    result = guard.check(
        "SELECT u.name, o.total FROM users u JOIN orders o ON u.id = o.user_id"
    )

    assert result.allowed is True


def test_schema_blocks_join_unknown_column_with_alias():
    guard = QueryGuard(
        GuardConfig(
            database_type="mysql",
            schema={
                "users": ["id", "name"],
                "orders": ["id", "user_id", "total"],
            },
            max_rows=None,
        )
    )

    result = guard.check(
        "SELECT u.name, o.secret FROM users u JOIN orders o ON u.id = o.user_id"
    )

    assert result.allowed is False
    assert "Column 'secret' is not in schema for table 'orders'" in result.errors


def test_select_star_is_blocked_by_default():
    guard = QueryGuard(
        GuardConfig(
            database_type="mysql",
            schema={"users": ["id", "name"]},
            max_rows=None,
        )
    )

    result = guard.check("SELECT * FROM users")

    assert result.allowed is False
    assert "SELECT * is not allowed" in result.errors


def test_table_star_is_blocked_by_default():
    guard = QueryGuard(
        GuardConfig(
            database_type="mysql",
            schema={"users": ["id", "name"]},
            max_rows=None,
        )
    )

    result = guard.check("SELECT users.* FROM users")

    assert result.allowed is False
    assert "SELECT * is not allowed" in result.errors


def test_select_star_can_be_allowed():
    guard = QueryGuard(
        GuardConfig(
            database_type="mysql",
            schema={"users": ["id", "name"]},
            allow_select_star=True,
            max_rows=None,
        )
    )

    result = guard.check("SELECT * FROM users")

    assert result.allowed is True


def test_count_star_is_allowed_when_select_star_is_blocked():
    guard = QueryGuard(
        GuardConfig(
            database_type="mysql",
            schema={"users": ["id", "name"]},
            allow_select_star=False,
            max_rows=None,
        )
    )

    result = guard.check("SELECT COUNT(*) FROM users")

    assert result.allowed is True


def test_select_without_expressions_is_blocked():
    guard = QueryGuard(GuardConfig(database_type="mysql"))

    result = guard.check("SELECT FROM users")

    assert result.allowed is False
    assert "SELECT query must include at least one expression" in result.errors


def test_select_from_malformed_qualified_table_without_expression_is_blocked():
    guard = QueryGuard(GuardConfig(database_type="mysql"))

    result = guard.check("SELECT FROM .tab.users")

    assert result.allowed is False
    assert "SELECT query must include at least one expression" in result.errors


def test_valid_constant_select_is_allowed():
    guard = QueryGuard(GuardConfig(database_type="mysql", max_rows=None))

    result = guard.check("SELECT 1")

    assert result.allowed is True


def test_select_without_expressions_is_blocked():
    guard = QueryGuard(GuardConfig(database_type="mysql"))

    result = guard.check("SELECT FROM users")

    assert result.allowed is False
    assert "SELECT query must include at least one expression" in result.errors


def test_select_star_without_from_is_blocked():
    guard = QueryGuard(GuardConfig(database_type="mysql"))

    result = guard.check("SELECT *")

    assert result.allowed is False
    assert "SELECT * requires a FROM clause" in result.errors


def test_select_constant_is_allowed():
    guard = QueryGuard(GuardConfig(database_type="mysql"))

    result = guard.check("SELECT 1")

    assert result.allowed is True


def test_bad_select_inside_cte_is_blocked():
    guard = QueryGuard(GuardConfig(database_type="mysql"))

    result = guard.check(
        """
        WITH bad_query AS (
            SELECT FROM users
        )
        SELECT * FROM bad_query
        """
    )

    assert result.allowed is False
    assert "SELECT query must include at least one expression" in result.errors


def test_bad_select_inside_union_is_blocked():
    guard = QueryGuard(GuardConfig(database_type="mysql"))

    result = guard.check(
        "SELECT id FROM users UNION SELECT FROM orders"
    )

    assert result.allowed is False
    assert "SELECT query must include at least one expression" in result.errors