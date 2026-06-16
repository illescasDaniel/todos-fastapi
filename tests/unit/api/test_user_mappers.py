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


def test_given_signup_body_when_mapping_to_entity_then_maps_fields(hasher: StubPasswordHasher) -> None:
	# given
	body = UserSignup(
		email="new@example.com",
		username="newuser",
		first_name="New",
		last_name="User",
		password="changeme",
	)

	# when
	entity = mappers.signup_to_entity(body, hasher)

	# then
	assert entity.id is None
	assert entity.email == "new@example.com"
	assert entity.hashed_password == "hashed:changeme"
	assert entity.is_active is True
	assert entity.role == "user"


def test_given_user_entity_when_mapping_to_response_then_maps_fields(existing_user: User) -> None:
	# given

	# when
	response = mappers.to_response(existing_user)

	# then
	assert response.id == TEST_USER_ID
	assert response.username == "jane"
	assert response.is_active is True


def test_given_self_replace_without_password_when_applying_then_keeps_existing_hash(
	existing_user: User,
	hasher: StubPasswordHasher,
) -> None:
	# given
	body = UserSelfReplace(
		email="jane@example.com",
		username="jane",
		first_name="Jane",
		last_name="Smith",
	)

	# when
	updated = mappers.apply_user_self_replace(existing_user, body, hasher)

	# then
	assert updated.last_name == "Smith"
	assert updated.hashed_password == "hashed:old"


def test_given_self_replace_with_new_password_when_applying_then_hashes_password(
	existing_user: User,
	hasher: StubPasswordHasher,
) -> None:
	# given
	body = UserSelfReplace(
		email="jane@example.com",
		username="jane",
		first_name="Jane",
		last_name="Smith",
		password="newsecret",
		current_password="old",
	)

	# when
	updated = mappers.apply_user_self_replace(existing_user, body, hasher)

	# then
	assert updated.hashed_password == "hashed:newsecret"


def test_given_password_change_without_current_password_when_self_replacing_then_raises_required(
	existing_user: User,
	hasher: StubPasswordHasher,
) -> None:
	"""M3: missing current_password raises CurrentPasswordRequiredError."""
	# given
	body = UserSelfReplace(
		email="jane@example.com",
		username="jane",
		first_name="Jane",
		last_name="Smith",
		password="newsecret",
	)

	# when
	with pytest.raises(CurrentPasswordRequiredError):
		mappers.apply_user_self_replace(existing_user, body, hasher)

	# then


def test_given_wrong_current_password_when_self_replacing_then_raises_invalid(
	existing_user: User,
	hasher: StubPasswordHasher,
) -> None:
	"""M3: wrong current_password raises CurrentPasswordInvalidError."""
	# given
	body = UserSelfReplace(
		email="jane@example.com",
		username="jane",
		first_name="Jane",
		last_name="Smith",
		password="newsecret",
		current_password="wrongpassword",
	)

	# when
	with pytest.raises(CurrentPasswordInvalidError):
		mappers.apply_user_self_replace(existing_user, body, hasher)

	# then


def test_given_admin_replace_body_when_applying_then_updates_role_and_active(
	existing_user: User,
	hasher: StubPasswordHasher,
) -> None:
	# given
	body = UserAdminReplace(
		email="jane@example.com",
		username="jane",
		first_name="Jane",
		last_name="Doe",
		role="admin",
		is_active=False,
	)

	# when
	updated = mappers.apply_user_admin_replace(existing_user, body, hasher)

	# then
	assert updated.role == "admin"
	assert updated.is_active is False
	assert updated.hashed_password == "hashed:old"


def test_given_partial_patch_fields_when_applying_to_user_then_merges_fields(
	existing_user: User,
	hasher: StubPasswordHasher,
) -> None:
	# given
	patch_fields = {"first_name": "Janet"}

	# when
	updated = mappers.apply_user_patch(existing_user, patch_fields, hasher)

	# then
	assert updated.first_name == "Janet"
	assert updated.last_name == "Doe"


def test_given_password_patch_with_current_password_when_applying_then_hashes_password(
	existing_user: User,
	hasher: StubPasswordHasher,
) -> None:
	"""M3: patch requires current_password when changing password."""
	# given
	patch_fields = {"password": "newsecret", "current_password": "old"}

	# when
	updated = mappers.apply_user_patch(existing_user, patch_fields, hasher)

	# then
	assert updated.hashed_password == "hashed:newsecret"


def test_given_password_patch_without_current_password_when_applying_then_raises_required(
	existing_user: User,
	hasher: StubPasswordHasher,
) -> None:
	"""M3: patch without current_password raises CurrentPasswordRequiredError."""
	# given
	patch_fields = {"password": "newsecret"}

	# when
	with pytest.raises(CurrentPasswordRequiredError):
		mappers.apply_user_patch(existing_user, patch_fields, hasher)

	# then


def test_given_partial_self_patch_body_when_extracting_fields_then_excludes_unset() -> None:
	# given
	body = UserSelfPatch(first_name="Janet")

	# when
	fields = mappers.self_patch_fields(body)

	# then
	assert fields == {"first_name": "Janet"}


def test_given_partial_admin_patch_body_when_extracting_fields_then_excludes_unset() -> None:
	# given
	body = UserAdminPatch(role="admin", is_active=False)

	# when
	fields = mappers.admin_patch_fields(body)

	# then
	assert fields == {"role": "admin", "is_active": False}
