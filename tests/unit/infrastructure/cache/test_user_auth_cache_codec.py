import pytest

from factories import TEST_USER_ID
from todos_app.domain.auth.authenticated_user import AuthenticatedUser
from todos_app.infrastructure.cache.user_auth_cache_codec import (
	auth_user_cache_key,
	deserialize_authenticated_user,
	serialize_authenticated_user,
)


pytestmark = pytest.mark.unit


def test_auth_user_cache_key_uses_uuid() -> None:
	assert auth_user_cache_key(TEST_USER_ID) == f"auth:user:{TEST_USER_ID}"


def test_serialize_and_deserialize_round_trip() -> None:
	user = AuthenticatedUser(user_id=TEST_USER_ID, username="jane", role="user")
	payload = serialize_authenticated_user(user)
	restored = deserialize_authenticated_user(payload)
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
def test_deserialize_rejects_invalid_payload(payload: str) -> None:
	assert deserialize_authenticated_user(payload) is None
