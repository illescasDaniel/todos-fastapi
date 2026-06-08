from todos_app.application.errors import InvalidCredentialsError
from todos_app.domain.auth.access_token_issuer import AccessTokenIssuer
from todos_app.domain.auth.password_hasher import PasswordHasher
from todos_app.domain.users.repository import UserRepository


async def authenticate(
	*,
	repo: UserRepository,
	hasher: PasswordHasher,
	issuer: AccessTokenIssuer,
	username: str,
	password: str,
) -> str:
	user = await repo.get_by_username(username)
	if user is None or user.id is None or not user.is_active or not hasher.verify(password, user.hashed_password):
		raise InvalidCredentialsError
	return issuer.issue(user_id=user.id, username=user.username, role=user.role)
