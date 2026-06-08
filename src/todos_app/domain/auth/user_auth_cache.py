from typing import Protocol
from uuid import UUID

from todos_app.domain.auth.authenticated_user import AuthenticatedUser


class UserAuthCache(Protocol):
	async def get_active_user(self, user_id: UUID) -> AuthenticatedUser | None: ...

	async def set_active_user(self, user: AuthenticatedUser, *, ttl_seconds: int) -> None: ...

	async def invalidate_user(self, user_id: UUID) -> None: ...
