import json
from uuid import UUID

from todos_app.domain.auth.authenticated_user import AuthenticatedUser


_AUTH_USER_KEY_PREFIX = "auth:user:"


def auth_user_cache_key(user_id: UUID) -> str:
	return f"{_AUTH_USER_KEY_PREFIX}{user_id}"


def serialize_authenticated_user(user: AuthenticatedUser) -> str:
	return json.dumps(
		{
			"user_id": str(user.user_id),
			"username": user.username,
			"role": user.role,
		}
	)


def deserialize_authenticated_user(payload: str) -> AuthenticatedUser | None:
	try:
		data = json.loads(payload)
	except json.JSONDecodeError:
		return None
	user_id_raw = data.get("user_id")
	username = data.get("username")
	role = data.get("role")
	if not isinstance(user_id_raw, str) or not isinstance(username, str) or not isinstance(role, str):
		return None
	try:
		user_id = UUID(user_id_raw)
	except ValueError:
		return None
	return AuthenticatedUser(user_id=user_id, username=username, role=role)
