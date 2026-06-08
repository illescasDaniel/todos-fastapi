from collections.abc import Callable
from uuid import UUID

from todos_app.application.errors import UserNotFoundError
from todos_app.domain.auth.user_auth_cache import UserAuthCache
from todos_app.domain.users.entity import User
from todos_app.domain.users.repository import UserRepository


async def create_user(entity: User, *, repo: UserRepository) -> User:
	return await repo.add(entity)


async def get_user_by_id(repo: UserRepository, user_id: UUID) -> User:
	user = await repo.get_by_id(user_id)
	if user is None:
		raise UserNotFoundError
	return user


async def _persist_user_update(
	repo: UserRepository,
	merged: User,
) -> User:
	updated = await repo.update(merged)
	if updated is None:
		raise UserNotFoundError
	return updated


async def update_user(
	user_id: UUID,
	merge: Callable[[User], User],
	*,
	repo: UserRepository,
	auth_cache: UserAuthCache,
) -> User:
	existing = await get_user_by_id(repo, user_id)
	updated = await _persist_user_update(repo, merge(existing))
	await auth_cache.invalidate_user(user_id)
	return updated


def _deactivated_user(existing: User) -> User:
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
	)


async def deactivate_user(
	user_id: UUID,
	*,
	repo: UserRepository,
	auth_cache: UserAuthCache,
) -> None:
	existing = await get_user_by_id(repo, user_id)
	await _persist_user_update(repo, _deactivated_user(existing))
	await auth_cache.invalidate_user(user_id)


async def hard_delete_user(
	user_id: UUID,
	*,
	repo: UserRepository,
	auth_cache: UserAuthCache,
) -> None:
	existing = await repo.get_by_id(user_id)
	if existing is None:
		raise UserNotFoundError
	deleted = await repo.delete(user_id)
	if not deleted:
		raise UserNotFoundError
	await auth_cache.invalidate_user(user_id)
