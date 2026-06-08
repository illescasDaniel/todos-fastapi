from uuid import UUID, uuid7


def new_id() -> UUID:
	return uuid7()


# Stable seed IDs for default_users.sql, default_todos.sql, docs/api.http, and docs.
JANE_USER_ID: UUID = UUID("019e7000-0000-7000-8000-000000000001")
ADMIN_USER_ID: UUID = UUID("019e7000-0000-7000-8000-000000000002")

SEED_TODO_IDS: tuple[UUID, ...] = (
	UUID("019e7000-0000-7000-8000-000000000003"),
	UUID("019e7000-0000-7000-8000-000000000004"),
	UUID("019e7000-0000-7000-8000-000000000005"),
)

# Sentinel for 404 tests — valid v7 shape, not used in seed data.
UNKNOWN_ID: UUID = UUID("019e7000-0000-7000-8000-000000000099")
