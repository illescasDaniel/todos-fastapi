from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from todos_app.domain.ids import JANE_USER_ID
from todos_app.domain.users.field_limits import (
	EMAIL_MAX_LENGTH,
	FIRST_NAME_MAX_LENGTH,
	LAST_NAME_MAX_LENGTH,
	PASSWORD_MAX_LENGTH,
	PASSWORD_MIN_LENGTH,
	USERNAME_MAX_LENGTH,
)


UserRole = Literal["user", "admin"]


_USERNAME_MIN_LENGTH = 2


class _UserProfileWithRole(BaseModel):
	email: EmailStr = Field(max_length=EMAIL_MAX_LENGTH)
	username: str = Field(min_length=_USERNAME_MIN_LENGTH, max_length=USERNAME_MAX_LENGTH)
	first_name: str = Field(max_length=FIRST_NAME_MAX_LENGTH)
	last_name: str = Field(max_length=LAST_NAME_MAX_LENGTH)
	role: UserRole


class UserSignup(BaseModel):
	model_config = ConfigDict(
		extra="forbid",
		json_schema_extra={
			"examples": [
				{
					"email": "jane@example.com",
					"username": "jane",
					"first_name": "Jane",
					"last_name": "Doe",
					"password": "changeme",
				}
			]
		},
	)

	email: EmailStr = Field(max_length=EMAIL_MAX_LENGTH)
	username: str = Field(min_length=_USERNAME_MIN_LENGTH, max_length=USERNAME_MAX_LENGTH)
	first_name: str = Field(max_length=FIRST_NAME_MAX_LENGTH)
	last_name: str = Field(max_length=LAST_NAME_MAX_LENGTH)
	password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)


class UserSelfReplace(BaseModel):
	model_config = ConfigDict(
		extra="forbid",
		json_schema_extra={
			"examples": [
				{
					"email": "jane@example.com",
					"username": "jane",
					"first_name": "Jane",
					"last_name": "Smith",
				}
			]
		},
	)

	email: EmailStr = Field(max_length=EMAIL_MAX_LENGTH)
	username: str = Field(min_length=_USERNAME_MIN_LENGTH, max_length=USERNAME_MAX_LENGTH)
	first_name: str = Field(max_length=FIRST_NAME_MAX_LENGTH)
	last_name: str = Field(max_length=LAST_NAME_MAX_LENGTH)
	password: str | None = Field(
		default=None,
		min_length=PASSWORD_MIN_LENGTH,
		max_length=PASSWORD_MAX_LENGTH,
		description="New password. Requires current_password when set.",
	)
	current_password: str | None = Field(
		default=None,
		description="Required when changing password (step-up auth).",
	)


class UserSelfPatch(BaseModel):
	model_config = ConfigDict(extra="forbid")

	email: EmailStr | None = Field(default=None, max_length=EMAIL_MAX_LENGTH)
	username: str | None = Field(default=None, min_length=_USERNAME_MIN_LENGTH, max_length=USERNAME_MAX_LENGTH)
	first_name: str | None = Field(default=None, max_length=FIRST_NAME_MAX_LENGTH)
	last_name: str | None = Field(default=None, max_length=LAST_NAME_MAX_LENGTH)
	password: str | None = Field(
		default=None,
		min_length=PASSWORD_MIN_LENGTH,
		max_length=PASSWORD_MAX_LENGTH,
		description="New password. Requires current_password when set.",
	)
	current_password: str | None = Field(
		default=None,
		description="Required when changing password (step-up auth).",
	)


class UserAdminReplace(_UserProfileWithRole):
	model_config = ConfigDict(
		extra="forbid",
		json_schema_extra={
			"examples": [
				{
					"email": "jane@example.com",
					"username": "jane",
					"first_name": "Jane",
					"last_name": "Smith",
					"password": "newsecret",
					"role": "admin",
					"is_active": True,
				}
			]
		},
	)

	is_active: bool
	password: str | None = Field(
		default=None,
		min_length=PASSWORD_MIN_LENGTH,
		max_length=PASSWORD_MAX_LENGTH,
		description="Omit to keep the current password.",
	)


class UserAdminPatch(BaseModel):
	model_config = ConfigDict(extra="forbid")

	email: EmailStr | None = Field(default=None, max_length=EMAIL_MAX_LENGTH)
	username: str | None = Field(default=None, min_length=_USERNAME_MIN_LENGTH, max_length=USERNAME_MAX_LENGTH)
	first_name: str | None = Field(default=None, max_length=FIRST_NAME_MAX_LENGTH)
	last_name: str | None = Field(default=None, max_length=LAST_NAME_MAX_LENGTH)
	password: str | None = Field(
		default=None,
		min_length=PASSWORD_MIN_LENGTH,
		max_length=PASSWORD_MAX_LENGTH,
	)
	role: UserRole | None = None
	is_active: bool | None = None


class UserResponse(BaseModel):
	model_config = ConfigDict(
		from_attributes=True,
		json_schema_extra={
			"examples": [
				{
					"id": str(JANE_USER_ID),
					"email": "jane@example.com",
					"username": "jane",
					"first_name": "Jane",
					"last_name": "Doe",
					"role": "user",
					"is_active": True,
				}
			]
		},
	)

	id: UUID
	email: EmailStr = Field(max_length=EMAIL_MAX_LENGTH)
	username: str = Field(max_length=USERNAME_MAX_LENGTH)
	first_name: str = Field(max_length=FIRST_NAME_MAX_LENGTH)
	last_name: str = Field(max_length=LAST_NAME_MAX_LENGTH)
	role: UserRole
	is_active: bool
