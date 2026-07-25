from uuid import UUID

from todos_app.auth.domain.user_auth_cache import UserAuthCache
from todos_app.users.application._support import guard_last_admin
from todos_app.users.application.errors import UserNotFoundError
from todos_app.users.domain.repository import UserRepository


async def hard_delete_user(
	user_id: UUID,
	*,
	repo: UserRepository,
	auth_cache: UserAuthCache,
) -> None:
	await guard_last_admin(user_id, repo)
	existing = await repo.get_by_id(user_id)
	if existing is None:
		raise UserNotFoundError
	deleted = await repo.delete(user_id)
	if not deleted:
		raise UserNotFoundError
	await auth_cache.invalidate_user(user_id)
