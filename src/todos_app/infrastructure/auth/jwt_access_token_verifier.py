from uuid import UUID

from jwt import PyJWTError
from jwt.api_jwt import decode  # pyright: ignore[reportUnknownVariableType]

from todos_app.core.settings import Settings
from todos_app.domain.auth.decoded_token import DecodedToken


class JwtAccessTokenVerifier:
	def __init__(self, settings: Settings) -> None:
		self._settings = settings

	def decode(self, token: str) -> DecodedToken | None:
		try:
			payload = decode(
				jwt=token,
				key=self._settings.jwt_secret_key,
				algorithms=["HS256"],
				audience=self._settings.jwt_audience,
				issuer=self._settings.jwt_issuer,
			)
		except PyJWTError:
			return None
		subject = payload.get("sub")
		username = payload.get("username")
		role = payload.get("role")
		token_version = payload.get("tvs")
		if not isinstance(subject, str) or not isinstance(username, str) or not isinstance(role, str):
			return None
		if not isinstance(token_version, int):
			return None
		try:
			user_id = UUID(subject)
		except ValueError:
			return None
		return DecodedToken(user_id=user_id, username=username, role=role, token_version=token_version)
