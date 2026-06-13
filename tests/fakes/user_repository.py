from uuid import UUID

from todos_app.domain.ids import new_id
from todos_app.domain.users.entity import User


class FakeUserRepository:
	def __init__(self, users: list[User] | None = None) -> None:
		self._users: dict[UUID, User] = {}
		self._by_username: dict[str, User] = {}
		if users:
			for user in users:
				if user.id is not None:
					self._users[user.id] = user
					self._by_username[user.username.lower()] = user

	async def add(self, user: User) -> User:
		new_user_id = new_id()
		stored = User(
			id=new_user_id,
			email=user.email,
			username=user.username.lower(),
			first_name=user.first_name,
			last_name=user.last_name,
			hashed_password=user.hashed_password,
			is_active=user.is_active,
			role=user.role,
			token_version=user.token_version,
		)
		self._users[new_user_id] = stored
		self._by_username[stored.username] = stored
		return stored

	async def update(self, user: User) -> User | None:
		if user.id is None or user.id not in self._users:
			return None
		old = self._users[user.id]
		if old.username != user.username.lower():
			del self._by_username[old.username]
			self._by_username[user.username.lower()] = user
		self._users[user.id] = user
		return user

	async def get_by_id(self, user_id: UUID) -> User | None:
		return self._users.get(user_id)

	async def get_by_username(self, username: str) -> User | None:
		return self._by_username.get(username.lower())

	async def delete(self, user_id: UUID) -> bool:
		user = self._users.pop(user_id, None)
		if user is None:
			return False
		self._by_username.pop(user.username.lower(), None)
		return True

	async def count_active_admins(self) -> int:
		return sum(1 for u in self._users.values() if u.role == "admin" and u.is_active)
