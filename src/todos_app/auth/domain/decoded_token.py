from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class DecodedToken:
	user_id: UUID
	username: str
	role: str
	token_version: int
