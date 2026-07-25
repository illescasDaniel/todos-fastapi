from collections.abc import Callable
from uuid import UUID

from todos_app.auth.domain.user_auth_cache import UserAuthCache
from todos_app.users.application._support import persist_user_update
from todos_app.users.application.get_user import get_user_by_id
from todos_app.users.domain.entity import User
from todos_app.users.domain.repository import UserRepository


async def update_user(
	user_id: UUID,
	merge: Callable[[User], User],
	*,
	repo: UserRepository,
	auth_cache: UserAuthCache,
) -> User:
	existing = await get_user_by_id(repo, user_id)
	merged = merge(existing)
	# H1: if the password changed, increment token_version to invalidate old JWTs.
	if merged.hashed_password != existing.hashed_password:
		merged = User(
			id=merged.id,
			email=merged.email,
			username=merged.username,
			first_name=merged.first_name,
			last_name=merged.last_name,
			hashed_password=merged.hashed_password,
			is_active=merged.is_active,
			role=merged.role,
			token_version=existing.token_version + 1,
		)
	updated = await persist_user_update(repo, merged)
	await auth_cache.invalidate_user(user_id)
	return updated
