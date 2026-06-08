from typing import Protocol
from uuid import UUID


class AccessTokenIssuer(Protocol):
	def issue(self, *, user_id: UUID, username: str, role: str) -> str: ...
