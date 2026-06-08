from typing import Any

from todos_app.api.users.schemas import (
	UserAdminPatch,
	UserAdminReplace,
	UserResponse,
	UserSelfPatch,
	UserSelfReplace,
	UserSignup,
)
from todos_app.domain.auth.password_hasher import PasswordHasher
from todos_app.domain.users.entity import User


def to_response(user: User) -> UserResponse:
	return UserResponse.model_validate(user)


def signup_to_entity(user: UserSignup, hasher: PasswordHasher) -> User:
	hashed_password = hasher.hash(user.password)
	return User(
		id=None,
		email=str(user.email),
		username=user.username,
		first_name=user.first_name,
		last_name=user.last_name,
		hashed_password=hashed_password,
		is_active=True,
		role="user",
	)


def _resolve_password(existing: User, password: str | None, hasher: PasswordHasher) -> str:
	if password is None:
		return existing.hashed_password
	return hasher.hash(password)


def apply_user_self_replace(existing: User, body: UserSelfReplace, hasher: PasswordHasher) -> User:
	if existing.id is None:
		raise ValueError("existing user must have an id")
	return User(
		id=existing.id,
		email=str(body.email),
		username=body.username,
		first_name=body.first_name,
		last_name=body.last_name,
		hashed_password=_resolve_password(existing, body.password, hasher),
		is_active=existing.is_active,
		role=existing.role,
	)


def apply_user_admin_replace(existing: User, body: UserAdminReplace, hasher: PasswordHasher) -> User:
	if existing.id is None:
		raise ValueError("existing user must have an id")
	return User(
		id=existing.id,
		email=str(body.email),
		username=body.username,
		first_name=body.first_name,
		last_name=body.last_name,
		hashed_password=_resolve_password(existing, body.password, hasher),
		is_active=body.is_active,
		role=body.role,
	)


def apply_user_patch(existing: User, fields: dict[str, Any], hasher: PasswordHasher) -> User:
	if existing.id is None:
		raise ValueError("existing user must have an id")
	hashed_password = existing.hashed_password
	if "password" in fields:
		password = fields["password"]
		if password is not None:
			hashed_password = hasher.hash(password)
	email = fields.get("email", existing.email)
	if email is None:
		email = existing.email
	else:
		email = str(email)
	return User(
		id=existing.id,
		email=email,
		username=fields.get("username", existing.username),
		first_name=fields.get("first_name", existing.first_name),
		last_name=fields.get("last_name", existing.last_name),
		hashed_password=hashed_password,
		is_active=fields.get("is_active", existing.is_active),
		role=fields.get("role", existing.role),
	)


def self_patch_fields(body: UserSelfPatch) -> dict[str, Any]:
	return body.model_dump(exclude_unset=True)


def admin_patch_fields(body: UserAdminPatch) -> dict[str, Any]:
	return body.model_dump(exclude_unset=True)
