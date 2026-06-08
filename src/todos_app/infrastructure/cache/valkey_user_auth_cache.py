from typing import TYPE_CHECKING
from uuid import UUID

from todos_app.domain.auth.authenticated_user import AuthenticatedUser
from todos_app.infrastructure.cache.user_auth_cache_codec import (
	auth_user_cache_key,
	deserialize_authenticated_user,
	serialize_authenticated_user,
)


if TYPE_CHECKING:
	from valkey.asyncio import Valkey


class ValkeyUserAuthCache:
	def __init__(self, client: Valkey) -> None:
		self._client = client

	async def get_active_user(self, user_id: UUID) -> AuthenticatedUser | None:
		payload = await self._client.get(auth_user_cache_key(user_id))
		if payload is None:
			return None
		return deserialize_authenticated_user(payload)

	async def set_active_user(self, user: AuthenticatedUser, *, ttl_seconds: int) -> None:
		await self._client.set(
			auth_user_cache_key(user.user_id),
			serialize_authenticated_user(user),
			ex=ttl_seconds,
		)

	async def invalidate_user(self, user_id: UUID) -> None:
		await self._client.delete(auth_user_cache_key(user_id))
