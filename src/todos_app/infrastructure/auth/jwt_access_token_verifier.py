from uuid import UUID

from jwt import PyJWTError
from jwt.api_jwt import decode  # pyright: ignore[reportUnknownVariableType]

from todos_app.core.settings import Settings
from todos_app.domain.auth.authenticated_user import AuthenticatedUser


class JwtAccessTokenVerifier:
	def __init__(self, settings: Settings) -> None:
		self._settings = settings

	def decode(self, token: str) -> AuthenticatedUser | None:
		try:
			payload = decode(
				jwt=token,
				key=self._settings.jwt_secret_key,
				algorithms=["HS256"],
			)
		except PyJWTError:
			return None
		subject = payload.get("sub")
		username = payload.get("username")
		role = payload.get("role")
		if not isinstance(subject, str) or not isinstance(username, str) or not isinstance(role, str):
			return None
		try:
			user_id = UUID(subject)
		except ValueError:
			return None
		return AuthenticatedUser(user_id=user_id, username=username, role=role)
