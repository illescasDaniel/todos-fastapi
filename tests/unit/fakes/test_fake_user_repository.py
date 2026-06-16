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


async def test_given_mixed_case_username_when_adding_user_then_lowercases_username() -> None:
	# given
	repo = FakeUserRepository()
	user = _user(username="Jane")

	# when
	created = await repo.add(user)

	# then
	assert created.username == "jane"
	found = await repo.get_by_username("JANE")
	assert found is not None
	assert found.id == created.id


async def test_given_mixed_case_username_when_updating_user_then_lowercases_username() -> None:
	# given
	repo = FakeUserRepository([_user(username="jane")])

	# when
	updated = await repo.update(_user(username="JANET"))

	# then
	assert updated is not None
	assert updated.username == "janet"
	stored = await repo.get_by_id(_USER_ID)
	assert stored is not None
	assert stored.username == "janet"
	found = await repo.get_by_username("JANET")
	assert found is not None
	assert found.id == _USER_ID


async def test_given_preloaded_mixed_case_username_when_initializing_repo_then_lowercases_username() -> None:
	# given
	user = _user(username="Jane")

	# when
	repo = FakeUserRepository([user])

	# then
	stored = await repo.get_by_id(_USER_ID)
	assert stored is not None
	assert stored.username == "jane"
	found = await repo.get_by_username("jane")
	assert found is not None
	assert found.id == _USER_ID
