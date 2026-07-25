ADMIN_ROLE = "admin"


class AdminRequiredError(Exception):
	pass


def _is_admin(actor_role: str) -> bool:
	return actor_role == ADMIN_ROLE


def require_admin(actor_role: str) -> None:
	if not _is_admin(actor_role):
		raise AdminRequiredError
