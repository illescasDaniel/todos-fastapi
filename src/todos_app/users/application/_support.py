from uuid import UUID

from todos_app.users.application.errors import LastAdminError, UserNotFoundError
from todos_app.users.domain.entity import User
from todos_app.users.domain.repository import UserRepository


async def persist_user_update(repo: UserRepository, merged: User) -> User:
	updated = await repo.update(merged)
	if updated is None:
		raise UserNotFoundError
	return updated


async def guard_last_admin(user_id: UUID, repo: UserRepository) -> None:
	"""L5: Raise LastAdminError when deleting/deactivating the last active admin."""
	target = await repo.get_by_id(user_id)
	if target is None or target.role != "admin" or not target.is_active:
		return
	count = await repo.count_active_admins()
	if count <= 1:
		raise LastAdminError


def deactivated_user(existing: User) -> User:
	if existing.id is None:
		raise ValueError("existing user must have an id")
	return User(
		id=existing.id,
		email=existing.email,
		username=existing.username,
		first_name=existing.first_name,
		last_name=existing.last_name,
		hashed_password=existing.hashed_password,
		is_active=False,
		role=existing.role,
		token_version=existing.token_version,
	)
