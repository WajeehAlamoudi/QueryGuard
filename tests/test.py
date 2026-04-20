from queryguard import (
    QueryGuard,
    GuardConfig)

config = GuardConfig(
    database_type="mysql",
    auto_fix_tables=True,
    schema={
        "users": ["id", "name"],
        "orders": ["id", "user_id"],
    }

)

guard = QueryGuard(config)

print(guard.check(sql="select 6 from .users;"))
