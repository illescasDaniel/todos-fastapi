import pytest

from factories import TEST_USER_ID
from fakes.user_repository import FakeUserRepository
from todos_app.application import auth as auth_use_cases
from todos_app.application.errors import InvalidCredentialsError
from todos_app.domain.users.entity import User


pytestmark = pytest.mark.unit


class FakePasswordHasher:
	def hash(self, plain_password: str) -> str:
		return f"hashed:{plain_password}"

	def verify(self, plain_password: str, hashed_password: str) -> bool:
		return hashed_password == self.hash(plain_password)


class FakeAccessTokenIssuer:
	def issue(self, *, user_id: object, username: str, role: str, token_version: int) -> str:
		return f"token:{user_id}:{username}:{role}:{token_version}"


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
				hashed_password="hashed:changeme",
				is_active=True,
				role="user",
			),
		]
	)


async def test_authenticate_returns_access_token(repo: FakeUserRepository) -> None:
	token = await auth_use_cases.authenticate(
		repo=repo,
		hasher=FakePasswordHasher(),
		issuer=FakeAccessTokenIssuer(),
		username="jane",
		password="changeme",
	)
	assert token == f"token:{TEST_USER_ID}:jane:user:0"


async def test_authenticate_raises_for_unknown_username(repo: FakeUserRepository) -> None:
	with pytest.raises(InvalidCredentialsError):
		await auth_use_cases.authenticate(
			repo=repo,
			hasher=FakePasswordHasher(),
			issuer=FakeAccessTokenIssuer(),
			username="missing",
			password="changeme",
		)


async def test_authenticate_raises_for_wrong_password(repo: FakeUserRepository) -> None:
	with pytest.raises(InvalidCredentialsError):
		await auth_use_cases.authenticate(
			repo=repo,
			hasher=FakePasswordHasher(),
			issuer=FakeAccessTokenIssuer(),
			username="jane",
			password="wrong",
		)


async def test_authenticate_raises_for_inactive_user(repo: FakeUserRepository) -> None:
	inactive = User(
		id=TEST_USER_ID,
		email="jane@example.com",
		username="jane",
		first_name="Jane",
		last_name="Doe",
		hashed_password="hashed:changeme",
		is_active=False,
		role="user",
	)
	repo = FakeUserRepository([inactive])
	with pytest.raises(InvalidCredentialsError):
		await auth_use_cases.authenticate(
			repo=repo,
			hasher=FakePasswordHasher(),
			issuer=FakeAccessTokenIssuer(),
			username="jane",
			password="changeme",
		)
