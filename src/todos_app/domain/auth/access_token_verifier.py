from typing import Protocol

from todos_app.domain.auth.decoded_token import DecodedToken


class AccessTokenVerifier(Protocol):
	def decode(self, token: str) -> DecodedToken | None: ...
