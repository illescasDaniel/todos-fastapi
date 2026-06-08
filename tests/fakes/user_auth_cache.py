from uuid import UUID

from todos_app.domain.auth.authenticated_user import AuthenticatedUser


class FakeUserAuthCache:
	def __init__(self) -> None:
		self._entries: dict[UUID, AuthenticatedUser] = {}
		self.invalidated: list[UUID] = []

	async def get_active_user(self, user_id: UUID) -> AuthenticatedUser | None:
		return self._entries.get(user_id)

	async def set_active_user(self, user: AuthenticatedUser, *, ttl_seconds: int) -> None:
		self._entries[user.user_id] = user

	async def invalidate_user(self, user_id: UUID) -> None:
		self.invalidated.append(user_id)
		self._entries.pop(user_id, None)
