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


async def test_create_user_persists_entity(repo: FakeUserRepository) -> None:
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
	created = await user_use_cases.create_user(entity, repo=repo)
	assert created.id is not None
	assert created.username == "newuser"


async def test_get_user_by_id_returns_user(repo: FakeUserRepository) -> None:
	user = await user_use_cases.get_user_by_id(repo, TEST_USER_ID)
	assert user.username == "jane"


async def test_get_user_by_id_raises_when_missing(repo: FakeUserRepository) -> None:
	with pytest.raises(UserNotFoundError):
		await user_use_cases.get_user_by_id(repo, UNKNOWN_ID)


async def test_update_user_applies_merge(repo: FakeUserRepository, auth_cache: FakeUserAuthCache) -> None:
	updated = await user_use_cases.update_user(
		TEST_USER_ID,
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
	assert updated.first_name == "Janet"
	assert auth_cache.invalidated == [TEST_USER_ID]


async def test_update_user_increments_token_version_on_password_change(
	repo: FakeUserRepository, auth_cache: FakeUserAuthCache
) -> None:
	"""H1: token_version is incremented when password changes."""
	updated = await user_use_cases.update_user(
		TEST_USER_ID,
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
	assert updated.token_version == 1


async def test_update_user_does_not_increment_token_version_without_password_change(
	repo: FakeUserRepository, auth_cache: FakeUserAuthCache
) -> None:
	"""H1: token_version stays the same when password is unchanged."""
	updated = await user_use_cases.update_user(
		TEST_USER_ID,
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
	assert updated.token_version == 0


async def test_update_user_raises_when_persist_returns_none(
	repo: FakeUserRepository,
	auth_cache: FakeUserAuthCache,
) -> None:
	with pytest.raises(UserNotFoundError):
		await user_use_cases.update_user(
			UNKNOWN_ID,
			lambda existing: existing,
			repo=repo,
			auth_cache=auth_cache,
		)


async def test_deactivate_user_sets_inactive(repo: FakeUserRepository, auth_cache: FakeUserAuthCache) -> None:
	await user_use_cases.deactivate_user(TEST_USER_ID, repo=repo, auth_cache=auth_cache)
	user = await repo.get_by_id(TEST_USER_ID)
	assert user is not None
	assert user.is_active is False
	assert auth_cache.invalidated == [TEST_USER_ID]


async def test_hard_delete_user_removes_user(repo: FakeUserRepository, auth_cache: FakeUserAuthCache) -> None:
	await user_use_cases.hard_delete_user(TEST_USER_ID, repo=repo, auth_cache=auth_cache)
	assert await repo.get_by_id(TEST_USER_ID) is None
	assert auth_cache.invalidated == [TEST_USER_ID]


async def test_hard_delete_user_raises_when_missing(auth_cache: FakeUserAuthCache) -> None:
	with pytest.raises(UserNotFoundError):
		await user_use_cases.hard_delete_user(UNKNOWN_ID, repo=FakeUserRepository(), auth_cache=auth_cache)


async def test_hard_delete_user_raises_when_delete_returns_false(auth_cache: FakeUserAuthCache) -> None:
	class DeleteFailsRepository(FakeUserRepository):
		async def delete(self, user_id: object) -> bool:
			return False

	repo = DeleteFailsRepository([_sample_user()])
	with pytest.raises(UserNotFoundError):
		await user_use_cases.hard_delete_user(TEST_USER_ID, repo=repo, auth_cache=auth_cache)


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


async def test_deactivate_last_admin_raises(auth_cache: FakeUserAuthCache) -> None:
	"""L5: Cannot deactivate the last active admin."""
	repo = FakeUserRepository([_admin_user(TEST_ADMIN_ID)])
	with pytest.raises(LastAdminError):
		await user_use_cases.deactivate_user(TEST_ADMIN_ID, repo=repo, auth_cache=auth_cache)


async def test_hard_delete_last_admin_raises(auth_cache: FakeUserAuthCache) -> None:
	"""L5: Cannot hard-delete the last active admin."""
	repo = FakeUserRepository([_admin_user(TEST_ADMIN_ID)])
	with pytest.raises(LastAdminError):
		await user_use_cases.hard_delete_user(TEST_ADMIN_ID, repo=repo, auth_cache=auth_cache)


async def test_deactivate_admin_with_another_admin_succeeds(auth_cache: FakeUserAuthCache) -> None:
	"""L5: Deactivating an admin is fine when another active admin exists."""
	from factories import TEST_ACTOR_ID

	repo = FakeUserRepository([_admin_user(TEST_ADMIN_ID), _admin_user(TEST_ACTOR_ID)])
	await user_use_cases.deactivate_user(TEST_ADMIN_ID, repo=repo, auth_cache=auth_cache)
	user = await repo.get_by_id(TEST_ADMIN_ID)
	assert user is not None
	assert not user.is_active
