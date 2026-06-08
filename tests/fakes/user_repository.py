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
					self._by_username[user.username] = user

	async def add(self, user: User) -> User:
		new_user_id = new_id()
		stored = User(
			id=new_user_id,
			email=user.email,
			username=user.username,
			first_name=user.first_name,
			last_name=user.last_name,
			hashed_password=user.hashed_password,
			is_active=user.is_active,
			role=user.role,
		)
		self._users[new_user_id] = stored
		self._by_username[stored.username] = stored
		return stored

	async def update(self, user: User) -> User | None:
		if user.id is None or user.id not in self._users:
			return None
		old = self._users[user.id]
		if old.username != user.username:
			del self._by_username[old.username]
			self._by_username[user.username] = user
		self._users[user.id] = user
		return user

	async def get_by_id(self, user_id: UUID) -> User | None:
		return self._users.get(user_id)

	async def get_by_username(self, username: str) -> User | None:
		return self._by_username.get(username)

	async def delete(self, user_id: UUID) -> bool:
		user = self._users.pop(user_id, None)
		if user is None:
			return False
		del self._by_username[user.username]
		return True
