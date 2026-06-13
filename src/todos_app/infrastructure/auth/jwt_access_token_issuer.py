from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt

from todos_app.core.settings import Settings
from todos_app.domain.ids import new_id


class JwtAccessTokenIssuer:
	def __init__(self, settings: Settings) -> None:
		self._settings = settings

	def issue(self, *, user_id: UUID, username: str, role: str, token_version: int) -> str:
		now = datetime.now(tz=timezone.utc)
		expires = now + timedelta(minutes=self._settings.jwt_expire_minutes)
		payload = {
			"sub": str(user_id),
			"username": username,
			"role": role,
			"tvs": token_version,
			"jti": str(new_id()),
			"iss": self._settings.jwt_issuer,
			"aud": self._settings.jwt_audience,
			"iat": now,
			"exp": expires,
		}
		return jwt.encode(payload=payload, key=self._settings.jwt_secret_key, algorithm=self._settings.jwt_algorithm)  # pyright: ignore[reportUnknownMemberType]
