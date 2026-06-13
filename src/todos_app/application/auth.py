from todos_app.application.errors import InvalidCredentialsError
from todos_app.domain.auth.access_token_issuer import AccessTokenIssuer
from todos_app.domain.auth.password_hasher import PasswordHasher
from todos_app.domain.users.repository import UserRepository


# Dummy Argon2 hash used to equalize timing when the username is not found (M1).
# The verify will always fail, but it burns approximately the same CPU as a real verify.
_DUMMY_HASH = "$argon2id$v=19$m=65536,t=3,p=4$c29tZXNhbHRzb21lc2FsdA$RoKUm4h6LtgLNZ5sNbTHKNEiFiJdLXCirBcfpvqCmVg"


async def authenticate(
	*,
	repo: UserRepository,
	hasher: PasswordHasher,
	issuer: AccessTokenIssuer,
	username: str,
	password: str,
) -> str:
	user = await repo.get_by_username(username.lower())
	if user is None:
		hasher.verify(password, _DUMMY_HASH)
		raise InvalidCredentialsError
	if user.id is None or not user.is_active or not hasher.verify(password, user.hashed_password):
		raise InvalidCredentialsError
	return issuer.issue(user_id=user.id, username=user.username, role=user.role, token_version=user.token_version)
