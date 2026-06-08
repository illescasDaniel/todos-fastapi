from dataclasses import dataclass
from uuid import UUID


@dataclass
class User:
	id: UUID | None
	email: str
	username: str
	first_name: str
	last_name: str
	hashed_password: str
	is_active: bool
	role: str
