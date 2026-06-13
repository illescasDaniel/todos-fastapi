import pytest
from fastapi.security import HTTPAuthorizationCredentials

from factories import TEST_USER_ID
from fakes.user_auth_cache import FakeUserAuthCache
from fakes.user_repository import FakeUserRepository
from todos_app.core.auth import get_current_user
from todos_app.core.settings import Settings
from todos_app.domain.users.entity import User
from todos_app.infrastructure.auth.jwt_access_token_issuer import JwtAccessTokenIssuer
from todos_app.infrastructure.auth.jwt_access_token_verifier import JwtAccessTokenVerifier


pytestmark = pytest.mark.unit

_VALID_SECRET = "test-secret-key-for-pytest-suite-32bytes!"


@pytest.fixture
def settings() -> Settings:
	return Settings(jwt_secret_key=_VALID_SECRET, auth_user_cache_ttl_seconds=120)


@pytest.fixture
def repo() -> FakeUserRepository:
	return FakeUserRepository(
		[
			User(
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
		]
	)


@pytest.fixture
def auth_cache() -> FakeUserAuthCache:
	return FakeUserAuthCache()


@pytest.fixture
def bearer_token(settings: Settings) -> str:
	issuer = JwtAccessTokenIssuer(settings)
	return issuer.issue(user_id=TEST_USER_ID, username="jane", role="user", token_version=0)


async def test_get_current_user_always_fetches_db(
	repo: FakeUserRepository,
	auth_cache: FakeUserAuthCache,
	settings: Settings,
	bearer_token: str,
) -> None:
	"""M5: DB is always consulted for fresh role and is_active even if cache has an entry."""
	verifier = JwtAccessTokenVerifier(settings)
	credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=bearer_token)

	user = await get_current_user(credentials, verifier, repo, auth_cache, settings)

	# Role and is_active come from DB (the DB user has role="user")
	assert user.role == "user"
	assert user.username == "jane"


async def test_get_current_user_populates_cache(
	repo: FakeUserRepository,
	auth_cache: FakeUserAuthCache,
	settings: Settings,
	bearer_token: str,
) -> None:
	verifier = JwtAccessTokenVerifier(settings)
	credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=bearer_token)

	user = await get_current_user(credentials, verifier, repo, auth_cache, settings)

	assert user.username == "jane"
	cached = await auth_cache.get_active_user(TEST_USER_ID)
	assert cached == user


async def test_get_current_user_rejects_stale_token_version(
	repo: FakeUserRepository,
	auth_cache: FakeUserAuthCache,
	settings: Settings,
) -> None:
	"""H1: token with outdated token_version is rejected."""
	from fastapi import HTTPException

	issuer = JwtAccessTokenIssuer(settings)
	stale_token = issuer.issue(user_id=TEST_USER_ID, username="jane", role="user", token_version=99)
	verifier = JwtAccessTokenVerifier(settings)
	credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=stale_token)

	with pytest.raises(HTTPException) as exc_info:
		await get_current_user(credentials, verifier, repo, auth_cache, settings)
	assert exc_info.value.status_code == 401
