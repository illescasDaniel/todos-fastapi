from uuid import UUID

import pytest

from fakes.user_repository import FakeUserRepository
from todos_app.domain.users.entity import User


pytestmark = pytest.mark.unit

_USER_ID = UUID("018f1234-5678-7890-abcd-ef1234567890")


def _user(*, username: str) -> User:
	return User(
		id=_USER_ID,
		email="jane@example.com",
		username=username,
		first_name="Jane",
		last_name="Doe",
		hashed_password="hashed",
		is_active=True,
		role="user",
		token_version=0,
	)


async def test_add_lowercases_username() -> None:
	repo = FakeUserRepository()
	created = await repo.add(_user(username="Jane"))

	assert created.username == "jane"
	found = await repo.get_by_username("JANE")
	assert found is not None
	assert found.id == created.id


async def test_update_lowercases_username() -> None:
	repo = FakeUserRepository([_user(username="jane")])
	updated = await repo.update(_user(username="JANET"))

	assert updated is not None
	assert updated.username == "janet"
	stored = await repo.get_by_id(_USER_ID)
	assert stored is not None
	assert stored.username == "janet"
	found = await repo.get_by_username("JANET")
	assert found is not None
	assert found.id == _USER_ID


async def test_init_lowercases_preloaded_usernames() -> None:
	repo = FakeUserRepository([_user(username="Jane")])

	stored = await repo.get_by_id(_USER_ID)
	assert stored is not None
	assert stored.username == "jane"
	found = await repo.get_by_username("jane")
	assert found is not None
	assert found.id == _USER_ID
