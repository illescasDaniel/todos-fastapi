import pytest

from factories import TEST_USER_ID
from todos_app.domain.auth.authenticated_user import AuthenticatedUser
from todos_app.infrastructure.cache.user_auth_cache_codec import (
	auth_user_cache_key,
	deserialize_authenticated_user,
	serialize_authenticated_user,
)


pytestmark = pytest.mark.unit


def test_given_user_id_when_building_cache_key_then_uses_uuid_prefix() -> None:
	# given
	user_id = TEST_USER_ID

	# when
	key = auth_user_cache_key(user_id)

	# then
	assert key == f"auth:user:{TEST_USER_ID}"


def test_given_authenticated_user_when_serializing_and_deserializing_then_round_trips() -> None:
	# given
	user = AuthenticatedUser(user_id=TEST_USER_ID, username="jane", role="user")

	# when
	payload = serialize_authenticated_user(user)
	restored = deserialize_authenticated_user(payload)

	# then
	assert restored == user


@pytest.mark.parametrize(
	"payload",
	[
		"not-json",
		"{}",
		'{"user_id":"not-a-uuid","username":"jane","role":"user"}',
		'{"user_id":"01932f8a-0000-7000-8000-000000000001","username":1,"role":"user"}',
	],
)
def test_given_invalid_cache_payload_when_deserializing_then_returns_none(payload: str) -> None:
	# given

	# when
	restored = deserialize_authenticated_user(payload)

	# then
	assert restored is None
