from typing import Protocol

from todos_app.domain.auth.authenticated_user import AuthenticatedUser


class AccessTokenVerifier(Protocol):
	def decode(self, token: str) -> AuthenticatedUser | None: ...
