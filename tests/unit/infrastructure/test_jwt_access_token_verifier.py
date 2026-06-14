import jwt
import pytest

from factories import TEST_USER_ID
from todos_app.core.settings import Settings
from todos_app.domain.ids import UNKNOWN_ID
from todos_app.infrastructure.auth.jwt_access_token_issuer import JwtAccessTokenIssuer
from todos_app.infrastructure.auth.jwt_access_token_verifier import JwtAccessTokenVerifier


pytestmark = pytest.mark.unit

_SETTINGS = Settings(jwt_secret_key="test-secret-key-for-pytest-suite-32bytes!")
_ISSUER = JwtAccessTokenIssuer(_SETTINGS)
_VERIFIER = JwtAccessTokenVerifier(_SETTINGS)


def test_decode_valid_token() -> None:
	token = _ISSUER.issue(user_id=TEST_USER_ID, username="jane", role="user", token_version=0)
	user = _VERIFIER.decode(token)
	assert user is not None
	assert user.user_id == TEST_USER_ID
	assert user.username == "jane"
	assert user.role == "user"
	assert user.token_version == 0


def test_decode_invalid_signature_returns_none() -> None:
	assert _VERIFIER.decode("not.a.valid.jwt") is None


def test_decode_non_string_claims_returns_none() -> None:
	token = jwt.encode(  # pyright: ignore[reportUnknownMemberType]
		{"sub": str(TEST_USER_ID), "username": 123, "role": "user"},
		key=_SETTINGS.jwt_secret_key,
		algorithm=_SETTINGS.jwt_algorithm,
	)
	assert _VERIFIER.decode(token) is None


def test_decode_invalid_uuid_subject_returns_none() -> None:
	token = jwt.encode(  # pyright: ignore[reportUnknownMemberType]
		{"sub": "not-a-uuid", "username": "jane", "role": "user"},
		key=_SETTINGS.jwt_secret_key,
		algorithm=_SETTINGS.jwt_algorithm,
	)
	assert _VERIFIER.decode(token) is None


def test_decode_invalid_username_type_returns_none() -> None:
	token = jwt.encode(  # pyright: ignore[reportUnknownMemberType]
		{"sub": str(TEST_USER_ID), "username": 123, "role": "user"},
		key=_SETTINGS.jwt_secret_key,
		algorithm=_SETTINGS.jwt_algorithm,
	)
	assert _VERIFIER.decode(token) is None


def test_decode_invalid_role_type_returns_none() -> None:
	token = jwt.encode(  # pyright: ignore[reportUnknownMemberType]
		{"sub": str(TEST_USER_ID), "username": "jane", "role": 99},
		key=_SETTINGS.jwt_secret_key,
		algorithm=_SETTINGS.jwt_algorithm,
	)
	assert _VERIFIER.decode(token) is None


def test_decode_unknown_user_id_still_parses() -> None:
	token = _ISSUER.issue(user_id=UNKNOWN_ID, username="ghost", role="user", token_version=0)
	user = _VERIFIER.decode(token)
	assert user is not None
	assert user.user_id == UNKNOWN_ID


def test_decode_missing_tvs_returns_none() -> None:
	import jwt as pyjwt

	token = pyjwt.encode(  # pyright: ignore[reportUnknownMemberType]
		{
			"sub": str(TEST_USER_ID),
			"username": "jane",
			"role": "user",
			"iss": _SETTINGS.jwt_issuer,
			"aud": _SETTINGS.jwt_audience,
		},
		key=_SETTINGS.jwt_secret_key,
		algorithm=_SETTINGS.jwt_algorithm,
	)
	assert _VERIFIER.decode(token) is None


def test_decode_token_version_preserved() -> None:
	token = _ISSUER.issue(user_id=TEST_USER_ID, username="jane", role="user", token_version=5)
	decoded = _VERIFIER.decode(token)
	assert decoded is not None
	assert decoded.token_version == 5
