import jwt
import pytest

from env_helpers import make_env_settings
from factories import TEST_USER_ID
from todos_app.domain.ids import UNKNOWN_ID
from todos_app.infrastructure.auth.jwt_access_token_issuer import JwtAccessTokenIssuer
from todos_app.infrastructure.auth.jwt_access_token_verifier import JwtAccessTokenVerifier


pytestmark = pytest.mark.unit

_HMAC_TEST_SECRET = "pytest-jwt-hmac-secret-key-sixty-four-bytes-minimum-length-ok!!!"
_SETTINGS = make_env_settings(jwt_secret_key="test-secret-key-for-pytest-suite-32bytes!")
_ISSUER = JwtAccessTokenIssuer(_SETTINGS)
_VERIFIER = JwtAccessTokenVerifier(_SETTINGS)


@pytest.mark.parametrize("algorithm", ["HS256", "HS384", "HS512"])
def test_given_hmac_algorithm_config_when_decoding_issued_token_then_returns_authenticated_user(
	algorithm: str,
) -> None:
	# given
	settings = make_env_settings(jwt_secret_key=_HMAC_TEST_SECRET, jwt_algorithm=algorithm)
	issuer = JwtAccessTokenIssuer(settings)
	verifier = JwtAccessTokenVerifier(settings)
	token = issuer.issue(user_id=TEST_USER_ID, username="jane", role="user", token_version=0)

	# when
	user = verifier.decode(token)

	# then
	assert user is not None
	assert user.user_id == TEST_USER_ID
	assert user.username == "jane"
	assert user.role == "user"
	assert user.token_version == 0


def test_given_valid_access_token_when_decoding_then_returns_authenticated_user() -> None:
	# given
	token = _ISSUER.issue(user_id=TEST_USER_ID, username="jane", role="user", token_version=0)

	# when
	user = _VERIFIER.decode(token)

	# then
	assert user is not None
	assert user.user_id == TEST_USER_ID
	assert user.username == "jane"
	assert user.role == "user"
	assert user.token_version == 0


def test_given_invalid_jwt_string_when_decoding_then_returns_none() -> None:
	# given
	token = "not.a.valid.jwt"

	# when
	user = _VERIFIER.decode(token)

	# then
	assert user is None


def test_given_non_string_username_claim_when_decoding_then_returns_none() -> None:
	# given
	token = jwt.encode(  # pyright: ignore[reportUnknownMemberType]
		{"sub": str(TEST_USER_ID), "username": 123, "role": "user"},
		key=_SETTINGS.jwt.secret_key,
		algorithm=_SETTINGS.jwt.algorithm,
	)

	# when
	user = _VERIFIER.decode(token)

	# then
	assert user is None


def test_given_invalid_uuid_subject_when_decoding_then_returns_none() -> None:
	# given
	token = jwt.encode(  # pyright: ignore[reportUnknownMemberType]
		{"sub": "not-a-uuid", "username": "jane", "role": "user"},
		key=_SETTINGS.jwt.secret_key,
		algorithm=_SETTINGS.jwt.algorithm,
	)

	# when
	user = _VERIFIER.decode(token)

	# then
	assert user is None


def test_given_non_string_username_in_token_when_decoding_then_returns_none() -> None:
	# given
	token = jwt.encode(  # pyright: ignore[reportUnknownMemberType]
		{"sub": str(TEST_USER_ID), "username": 123, "role": "user"},
		key=_SETTINGS.jwt.secret_key,
		algorithm=_SETTINGS.jwt.algorithm,
	)

	# when
	user = _VERIFIER.decode(token)

	# then
	assert user is None


def test_given_non_string_role_claim_when_decoding_then_returns_none() -> None:
	# given
	token = jwt.encode(  # pyright: ignore[reportUnknownMemberType]
		{"sub": str(TEST_USER_ID), "username": "jane", "role": 99},
		key=_SETTINGS.jwt.secret_key,
		algorithm=_SETTINGS.jwt.algorithm,
	)

	# when
	user = _VERIFIER.decode(token)

	# then
	assert user is None


def test_given_unknown_user_id_in_token_when_decoding_then_still_parses() -> None:
	# given
	token = _ISSUER.issue(user_id=UNKNOWN_ID, username="ghost", role="user", token_version=0)

	# when
	user = _VERIFIER.decode(token)

	# then
	assert user is not None
	assert user.user_id == UNKNOWN_ID


def test_given_missing_token_version_claim_when_decoding_then_returns_none() -> None:
	# given
	import jwt as pyjwt

	token = pyjwt.encode(  # pyright: ignore[reportUnknownMemberType]
		{
			"sub": str(TEST_USER_ID),
			"username": "jane",
			"role": "user",
			"iss": _SETTINGS.jwt.issuer,
			"aud": _SETTINGS.jwt.audience,
		},
		key=_SETTINGS.jwt.secret_key,
		algorithm=_SETTINGS.jwt.algorithm,
	)

	# when
	user = _VERIFIER.decode(token)

	# then
	assert user is None


def test_given_non_zero_token_version_when_decoding_then_preserves_version() -> None:
	# given
	token = _ISSUER.issue(user_id=TEST_USER_ID, username="jane", role="user", token_version=5)

	# when
	decoded = _VERIFIER.decode(token)

	# then
	assert decoded is not None
	assert decoded.token_version == 5
