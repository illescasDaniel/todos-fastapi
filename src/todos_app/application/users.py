from collections.abc import Callable
from uuid import UUID

from todos_app.application.errors import LastAdminError, UserNotFoundError
from todos_app.domain.auth.user_auth_cache import UserAuthCache
from todos_app.domain.users.entity import User
from todos_app.domain.users.repository import UserRepository


async def create_user(entity: User, *, repo: UserRepository) -> User:
	normalized = User(
		id=entity.id,
		email=entity.email,
		username=entity.username.lower(),
		first_name=entity.first_name,
		last_name=entity.last_name,
		hashed_password=entity.hashed_password,
		is_active=entity.is_active,
		role=entity.role,
		token_version=entity.token_version,
	)
	return await repo.add(normalized)


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
	updated = await _persist_user_update(repo, merged)
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
		token_version=existing.token_version,
	)


async def _guard_last_admin(user_id: UUID, repo: UserRepository) -> None:
	"""L5: Raise LastAdminError when deleting/deactivating the last active admin."""
	target = await repo.get_by_id(user_id)
	if target is None or target.role != "admin" or not target.is_active:
		return
	count = await repo.count_active_admins()
	if count <= 1:
		raise LastAdminError


async def deactivate_user(
	user_id: UUID,
	*,
	repo: UserRepository,
	auth_cache: UserAuthCache,
) -> None:
	await _guard_last_admin(user_id, repo)
	existing = await get_user_by_id(repo, user_id)
	await _persist_user_update(repo, _deactivated_user(existing))
	await auth_cache.invalidate_user(user_id)


async def hard_delete_user(
	user_id: UUID,
	*,
	repo: UserRepository,
	auth_cache: UserAuthCache,
) -> None:
	await _guard_last_admin(user_id, repo)
	existing = await repo.get_by_id(user_id)
	if existing is None:
		raise UserNotFoundError
	deleted = await repo.delete(user_id)
	if not deleted:
		raise UserNotFoundError
	await auth_cache.invalidate_user(user_id)
