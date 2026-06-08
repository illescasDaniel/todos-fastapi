from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class AuthenticatedUser:
	user_id: UUID
	username: str
	role: str
