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
		expires = now + timedelta(minutes=self._settings.jwt.expire_minutes)
		payload = {
			"sub": str(user_id),
			"username": username,
			"role": role,
			"tvs": token_version,
			"jti": str(new_id()),
			"iss": self._settings.jwt.issuer,
			"aud": self._settings.jwt.audience,
			"iat": now,
			"exp": expires,
		}
		return jwt.encode(payload=payload, key=self._settings.jwt.secret_key, algorithm=self._settings.jwt.algorithm)  # pyright: ignore[reportUnknownMemberType]
