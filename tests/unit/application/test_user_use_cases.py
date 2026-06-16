import pytest

from factories import TEST_ADMIN_ID, TEST_USER_ID
from fakes.user_auth_cache import FakeUserAuthCache
from fakes.user_repository import FakeUserRepository
from todos_app.application import users as user_use_cases
from todos_app.application.errors import LastAdminError, UserNotFoundError
from todos_app.domain.ids import UNKNOWN_ID
from todos_app.domain.users.entity import User


pytestmark = pytest.mark.unit


def _sample_user(**overrides: object) -> User:
	base = User(
		id=TEST_USER_ID,
		email="jane@example.com",
		username="jane",
		first_name="Jane",
		last_name="Doe",
		hashed_password="hashed",
		is_active=True,
		role="user",
		token_version=0,
	)
	for key, value in overrides.items():
		setattr(base, key, value)
	return base


@pytest.fixture
def repo() -> FakeUserRepository:
	return FakeUserRepository([_sample_user()])


@pytest.fixture
def auth_cache() -> FakeUserAuthCache:
	return FakeUserAuthCache()


async def test_given_new_user_entity_when_creating_user_then_persists_with_id(
	repo: FakeUserRepository,
) -> None:
	# given
	entity = User(
		id=None,
		email="new@example.com",
		username="newuser",
		first_name="New",
		last_name="User",
		hashed_password="hashed",
		is_active=True,
		role="user",
	)

	# when
	created = await user_use_cases.create_user(entity, repo=repo)

	# then
	assert created.id is not None
	assert created.username == "newuser"


async def test_given_existing_user_id_when_getting_by_id_then_returns_user(
	repo: FakeUserRepository,
) -> None:
	# given
	user_id = TEST_USER_ID

	# when
	user = await user_use_cases.get_user_by_id(repo, user_id)

	# then
	assert user.username == "jane"


async def test_given_unknown_user_id_when_getting_by_id_then_raises_not_found(
	repo: FakeUserRepository,
) -> None:
	# given
	user_id = UNKNOWN_ID

	# when
	with pytest.raises(UserNotFoundError):
		await user_use_cases.get_user_by_id(repo, user_id)

	# then


async def test_given_profile_change_when_updating_user_then_applies_merge_and_invalidates_cache(
	repo: FakeUserRepository,
	auth_cache: FakeUserAuthCache,
) -> None:
	# given
	user_id = TEST_USER_ID

	# when
	updated = await user_use_cases.update_user(
		user_id,
		lambda existing: User(
			id=existing.id,
			email=existing.email,
			username=existing.username,
			first_name="Janet",
			last_name=existing.last_name,
			hashed_password=existing.hashed_password,
			is_active=existing.is_active,
			role=existing.role,
			token_version=existing.token_version,
		),
		repo=repo,
		auth_cache=auth_cache,
	)

	# then
	assert updated.first_name == "Janet"
	assert auth_cache.invalidated == [TEST_USER_ID]


async def test_given_password_change_when_updating_user_then_increments_token_version(
	repo: FakeUserRepository,
	auth_cache: FakeUserAuthCache,
) -> None:
	"""H1: token_version is incremented when password changes."""
	# given
	user_id = TEST_USER_ID

	# when
	updated = await user_use_cases.update_user(
		user_id,
		lambda existing: User(
			id=existing.id,
			email=existing.email,
			username=existing.username,
			first_name=existing.first_name,
			last_name=existing.last_name,
			hashed_password="new-hash",
			is_active=existing.is_active,
			role=existing.role,
			token_version=existing.token_version,
		),
		repo=repo,
		auth_cache=auth_cache,
	)

	# then
	assert updated.token_version == 1


async def test_given_non_password_change_when_updating_user_then_keeps_token_version(
	repo: FakeUserRepository,
	auth_cache: FakeUserAuthCache,
) -> None:
	"""H1: token_version stays the same when password is unchanged."""
	# given
	user_id = TEST_USER_ID

	# when
	updated = await user_use_cases.update_user(
		user_id,
		lambda existing: User(
			id=existing.id,
			email=existing.email,
			username=existing.username,
			first_name="Janet",
			last_name=existing.last_name,
			hashed_password=existing.hashed_password,
			is_active=existing.is_active,
			role=existing.role,
			token_version=existing.token_version,
		),
		repo=repo,
		auth_cache=auth_cache,
	)

	# then
	assert updated.token_version == 0


async def test_given_unknown_user_id_when_updating_user_then_raises_not_found(
	repo: FakeUserRepository,
	auth_cache: FakeUserAuthCache,
) -> None:
	# given
	user_id = UNKNOWN_ID

	# when
	with pytest.raises(UserNotFoundError):
		await user_use_cases.update_user(
			user_id,
			lambda existing: existing,
			repo=repo,
			auth_cache=auth_cache,
		)

	# then


async def test_given_active_user_when_deactivating_then_sets_inactive_and_invalidates_cache(
	repo: FakeUserRepository,
	auth_cache: FakeUserAuthCache,
) -> None:
	# given
	user_id = TEST_USER_ID

	# when
	await user_use_cases.deactivate_user(user_id, repo=repo, auth_cache=auth_cache)

	# then
	user = await repo.get_by_id(TEST_USER_ID)
	assert user is not None
	assert user.is_active is False
	assert auth_cache.invalidated == [TEST_USER_ID]


async def test_given_existing_user_when_hard_deleting_then_removes_user_and_invalidates_cache(
	repo: FakeUserRepository,
	auth_cache: FakeUserAuthCache,
) -> None:
	# given
	user_id = TEST_USER_ID

	# when
	await user_use_cases.hard_delete_user(user_id, repo=repo, auth_cache=auth_cache)

	# then
	assert await repo.get_by_id(TEST_USER_ID) is None
	assert auth_cache.invalidated == [TEST_USER_ID]


async def test_given_unknown_user_id_when_hard_deleting_then_raises_not_found(
	auth_cache: FakeUserAuthCache,
) -> None:
	# given
	repo = FakeUserRepository()

	# when
	with pytest.raises(UserNotFoundError):
		await user_use_cases.hard_delete_user(UNKNOWN_ID, repo=repo, auth_cache=auth_cache)

	# then


async def test_given_delete_returns_false_when_hard_deleting_then_raises_not_found(
	auth_cache: FakeUserAuthCache,
) -> None:
	# given
	class DeleteFailsRepository(FakeUserRepository):
		async def delete(self, user_id: object) -> bool:
			return False

	repo = DeleteFailsRepository([_sample_user()])

	# when
	with pytest.raises(UserNotFoundError):
		await user_use_cases.hard_delete_user(TEST_USER_ID, repo=repo, auth_cache=auth_cache)

	# then


def _admin_user(user_id: object = None, is_active: bool = True) -> User:
	from uuid import UUID

	uid = user_id if isinstance(user_id, UUID) else TEST_ADMIN_ID
	return User(
		id=uid,
		email=f"admin-{uid}@example.com",
		username=f"admin-{uid}",
		first_name="Admin",
		last_name="User",
		hashed_password="hashed",
		is_active=is_active,
		role="admin",
		token_version=0,
	)


async def test_given_last_active_admin_when_deactivating_then_raises_last_admin_error(
	auth_cache: FakeUserAuthCache,
) -> None:
	"""L5: Cannot deactivate the last active admin."""
	# given
	repo = FakeUserRepository([_admin_user(TEST_ADMIN_ID)])

	# when
	with pytest.raises(LastAdminError):
		await user_use_cases.deactivate_user(TEST_ADMIN_ID, repo=repo, auth_cache=auth_cache)

	# then


async def test_given_last_active_admin_when_hard_deleting_then_raises_last_admin_error(
	auth_cache: FakeUserAuthCache,
) -> None:
	"""L5: Cannot hard-delete the last active admin."""
	# given
	repo = FakeUserRepository([_admin_user(TEST_ADMIN_ID)])

	# when
	with pytest.raises(LastAdminError):
		await user_use_cases.hard_delete_user(TEST_ADMIN_ID, repo=repo, auth_cache=auth_cache)

	# then


async def test_given_another_active_admin_when_deactivating_admin_then_succeeds(
	auth_cache: FakeUserAuthCache,
) -> None:
	"""L5: Deactivating an admin is fine when another active admin exists."""
	# given
	from factories import TEST_ACTOR_ID

	repo = FakeUserRepository([_admin_user(TEST_ADMIN_ID), _admin_user(TEST_ACTOR_ID)])

	# when
	await user_use_cases.deactivate_user(TEST_ADMIN_ID, repo=repo, auth_cache=auth_cache)

	# then
	user = await repo.get_by_id(TEST_ADMIN_ID)
	assert user is not None
	assert not user.is_active
