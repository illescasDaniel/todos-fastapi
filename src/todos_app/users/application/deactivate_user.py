from uuid import UUID

from todos_app.auth.domain.user_auth_cache import UserAuthCache
from todos_app.users.application._support import deactivated_user, guard_last_admin, persist_user_update
from todos_app.users.application.get_user import get_user_by_id
from todos_app.users.domain.repository import UserRepository


async def deactivate_user(
	user_id: UUID,
	*,
	repo: UserRepository,
	auth_cache: UserAuthCache,
) -> None:
	await guard_last_admin(user_id, repo)
	existing = await get_user_by_id(repo, user_id)
	await persist_user_update(repo, deactivated_user(existing))
	await auth_cache.invalidate_user(user_id)
