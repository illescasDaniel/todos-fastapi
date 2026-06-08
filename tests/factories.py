import uuid
from typing import Any
from uuid import UUID


def unique_suffix() -> str:
	return uuid.uuid4().hex[:8]


def user_signup_payload(**overrides: Any) -> dict[str, Any]:
	suffix = unique_suffix()
	base: dict[str, Any] = {
		"email": f"user-{suffix}@example.com",
		"username": f"user-{suffix}",
		"first_name": "Test",
		"last_name": "User",
		"password": "changeme",
	}
	base.update(overrides)
	return base


def todo_create_payload(**overrides: Any) -> dict[str, Any]:
	base: dict[str, Any] = {
		"title": "Test todo",
		"description": "Test description",
		"priority": "medium",
		"completed": False,
	}
	base.update(overrides)
	return base


# Fixed UUIDs for unit tests (valid v7 shape, monotonically increasing).
TEST_USER_ID: UUID = UUID("019e7000-0000-7000-8000-000000000011")
TEST_USER_ID_B: UUID = UUID("019e7000-0000-7000-8000-000000000012")
TEST_TODO_ID: UUID = UUID("019e7000-0000-7000-8000-000000000021")
TEST_TODO_ID_B: UUID = UUID("019e7000-0000-7000-8000-000000000022")
TEST_ACTOR_ID: UUID = UUID("019e7000-0000-7000-8000-000000000031")
TEST_ACTOR_ID_B: UUID = UUID("019e7000-0000-7000-8000-000000000032")
TEST_ADMIN_ID: UUID = UUID("019e7000-0000-7000-8000-000000000033")
