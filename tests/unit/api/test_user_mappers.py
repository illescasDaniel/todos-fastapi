import pytest

from factories import TEST_USER_ID
from todos_app.api.users import mappers
from todos_app.api.users.schemas import (
	UserAdminPatch,
	UserAdminReplace,
	UserSelfPatch,
	UserSelfReplace,
	UserSignup,
)
from todos_app.application.errors import CurrentPasswordInvalidError, CurrentPasswordRequiredError
from todos_app.domain.users.entity import User


pytestmark = pytest.mark.unit


class StubPasswordHasher:
	def hash(self, plain_password: str) -> str:
		return f"hashed:{plain_password}"

	def verify(self, plain_password: str, hashed_password: str) -> bool:
		return hashed_password == f"hashed:{plain_password}"


@pytest.fixture
def hasher() -> StubPasswordHasher:
	return StubPasswordHasher()


@pytest.fixture
def existing_user() -> User:
	return User(
		id=TEST_USER_ID,
		email="jane@example.com",
		username="jane",
		first_name="Jane",
		last_name="Doe",
		hashed_password="hashed:old",
		is_active=True,
		role="user",
		token_version=0,
	)


def test_signup_to_entity_maps_fields(hasher: StubPasswordHasher) -> None:
	body = UserSignup(
		email="new@example.com",
		username="newuser",
		first_name="New",
		last_name="User",
		password="changeme",
	)
	entity = mappers.signup_to_entity(body, hasher)
	assert entity.id is None
	assert entity.email == "new@example.com"
	assert entity.hashed_password == "hashed:changeme"
	assert entity.is_active is True
	assert entity.role == "user"


def test_to_response_maps_entity(existing_user: User) -> None:
	response = mappers.to_response(existing_user)
	assert response.id == TEST_USER_ID
	assert response.username == "jane"
	assert response.is_active is True


def test_apply_user_self_replace_keeps_password_when_omitted(
	existing_user: User,
	hasher: StubPasswordHasher,
) -> None:
	body = UserSelfReplace(
		email="jane@example.com",
		username="jane",
		first_name="Jane",
		last_name="Smith",
	)
	updated = mappers.apply_user_self_replace(existing_user, body, hasher)
	assert updated.last_name == "Smith"
	assert updated.hashed_password == "hashed:old"


def test_apply_user_self_replace_hashes_new_password(
	existing_user: User,
	hasher: StubPasswordHasher,
) -> None:
	body = UserSelfReplace(
		email="jane@example.com",
		username="jane",
		first_name="Jane",
		last_name="Smith",
		password="newsecret",
		current_password="old",
	)
	updated = mappers.apply_user_self_replace(existing_user, body, hasher)
	assert updated.hashed_password == "hashed:newsecret"


def test_apply_user_self_replace_requires_current_password(
	existing_user: User,
	hasher: StubPasswordHasher,
) -> None:
	"""M3: missing current_password raises CurrentPasswordRequiredError."""
	body = UserSelfReplace(
		email="jane@example.com",
		username="jane",
		first_name="Jane",
		last_name="Smith",
		password="newsecret",
	)
	with pytest.raises(CurrentPasswordRequiredError):
		mappers.apply_user_self_replace(existing_user, body, hasher)


def test_apply_user_self_replace_rejects_wrong_current_password(
	existing_user: User,
	hasher: StubPasswordHasher,
) -> None:
	"""M3: wrong current_password raises CurrentPasswordInvalidError."""
	body = UserSelfReplace(
		email="jane@example.com",
		username="jane",
		first_name="Jane",
		last_name="Smith",
		password="newsecret",
		current_password="wrongpassword",
	)
	with pytest.raises(CurrentPasswordInvalidError):
		mappers.apply_user_self_replace(existing_user, body, hasher)


def test_apply_user_admin_replace_updates_role_and_active(
	existing_user: User,
	hasher: StubPasswordHasher,
) -> None:
	body = UserAdminReplace(
		email="jane@example.com",
		username="jane",
		first_name="Jane",
		last_name="Doe",
		role="admin",
		is_active=False,
	)
	updated = mappers.apply_user_admin_replace(existing_user, body, hasher)
	assert updated.role == "admin"
	assert updated.is_active is False
	assert updated.hashed_password == "hashed:old"


def test_apply_user_patch_partial_fields(existing_user: User, hasher: StubPasswordHasher) -> None:
	updated = mappers.apply_user_patch(existing_user, {"first_name": "Janet"}, hasher)
	assert updated.first_name == "Janet"
	assert updated.last_name == "Doe"


def test_apply_user_patch_hashes_password_when_set(existing_user: User, hasher: StubPasswordHasher) -> None:
	"""M3: patch requires current_password when changing password."""
	updated = mappers.apply_user_patch(existing_user, {"password": "newsecret", "current_password": "old"}, hasher)
	assert updated.hashed_password == "hashed:newsecret"


def test_apply_user_patch_raises_without_current_password(existing_user: User, hasher: StubPasswordHasher) -> None:
	"""M3: patch without current_password raises CurrentPasswordRequiredError."""
	with pytest.raises(CurrentPasswordRequiredError):
		mappers.apply_user_patch(existing_user, {"password": "newsecret"}, hasher)


def test_self_patch_fields_excludes_unset() -> None:
	body = UserSelfPatch(first_name="Janet")
	fields = mappers.self_patch_fields(body)
	assert fields == {"first_name": "Janet"}


def test_admin_patch_fields_excludes_unset() -> None:
	body = UserAdminPatch(role="admin", is_active=False)
	fields = mappers.admin_patch_fields(body)
	assert fields == {"role": "admin", "is_active": False}
