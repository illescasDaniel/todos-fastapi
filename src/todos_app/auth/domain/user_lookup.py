from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True)
class UserCredentials:
	"""Minimal identity fields needed for login (auth-owned; not the users entity)."""

	id: UUID
	username: str
	hashed_password: str
	is_active: bool
	role: str
	token_version: int


class UserLookup(Protocol):
	async def get_by_username(self, username: str) -> UserCredentials | None: ...
