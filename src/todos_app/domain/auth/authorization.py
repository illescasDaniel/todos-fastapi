from uuid import UUID


ADMIN_ROLE = "admin"


class AdminRequiredError(Exception):
	pass


def is_admin(actor_role: str) -> bool:
	return actor_role == ADMIN_ROLE


def require_admin(actor_role: str) -> None:
	if not is_admin(actor_role):
		raise AdminRequiredError


def list_owner_filter(*, actor_id: UUID, actor_role: str) -> UUID | None:
	"""Return owner_id to filter by, or None when the actor may see all todos."""
	return None if actor_role == ADMIN_ROLE else actor_id


def resolve_create_owner_id(*, actor_id: UUID, actor_role: str, requested_owner_id: UUID | None) -> UUID:
	if actor_role == ADMIN_ROLE:
		return requested_owner_id if requested_owner_id is not None else actor_id
	return actor_id


def is_update_owner_change_forbidden(
	*,
	actor_role: str,
	existing_owner_id: UUID,
	requested_owner_id: UUID | None,
) -> bool:
	return actor_role != ADMIN_ROLE and requested_owner_id is not None and requested_owner_id != existing_owner_id


def resolve_update_owner_id(*, existing_owner_id: UUID, requested_owner_id: UUID | None) -> UUID:
	return requested_owner_id if requested_owner_id is not None else existing_owner_id
