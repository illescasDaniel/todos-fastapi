from typing import Literal

from pydantic import BaseModel

from todos_app.api.auth.schemas import LoginRequest, TokenResponse
from todos_app.api.todos.schemas import (
	TodoCreate,
	TodoListResponse,
	TodoPatch,
	TodoResponse,
	TodoUpdate,
)
from todos_app.api.users.schemas import (
	UserAdminPatch,
	UserAdminReplace,
	UserResponse,
	UserSelfPatch,
	UserSelfReplace,
	UserSignup,
)


SchemaExportMode = Literal["validation", "serialization"]

SchemaGroup = Literal["auth", "todos", "users"]


class RegisteredSchema:
	__slots__ = ("name", "model", "group", "description")

	def __init__(
		self,
		*,
		name: str,
		model: type[BaseModel],
		group: SchemaGroup,
		description: str,
	) -> None:
		self.name = name
		self.model = model
		self.group = group
		self.description = description


PUBLIC_API_SCHEMAS: tuple[RegisteredSchema, ...] = (
	RegisteredSchema(
		name="LoginRequest",
		model=LoginRequest,
		group="auth",
		description="Credentials for POST /auth/login.",
	),
	RegisteredSchema(
		name="TokenResponse",
		model=TokenResponse,
		group="auth",
		description="JWT access token returned by POST /auth/login.",
	),
	RegisteredSchema(
		name="TodoCreate",
		model=TodoCreate,
		group="todos",
		description="Body for POST /todos.",
	),
	RegisteredSchema(
		name="TodoUpdate",
		model=TodoUpdate,
		group="todos",
		description="Body for PUT /todos/{todo_id}.",
	),
	RegisteredSchema(
		name="TodoPatch",
		model=TodoPatch,
		group="todos",
		description="Body for PATCH /todos/{todo_id}.",
	),
	RegisteredSchema(
		name="TodoResponse",
		model=TodoResponse,
		group="todos",
		description="Single todo in API responses.",
	),
	RegisteredSchema(
		name="TodoListResponse",
		model=TodoListResponse,
		group="todos",
		description="Cursor-paginated list from GET /todos.",
	),
	RegisteredSchema(
		name="UserSignup",
		model=UserSignup,
		group="users",
		description="Body for POST /users (public signup).",
	),
	RegisteredSchema(
		name="UserSelfReplace",
		model=UserSelfReplace,
		group="users",
		description="Body for PUT /users/me.",
	),
	RegisteredSchema(
		name="UserSelfPatch",
		model=UserSelfPatch,
		group="users",
		description="Body for PATCH /users/me.",
	),
	RegisteredSchema(
		name="UserAdminReplace",
		model=UserAdminReplace,
		group="users",
		description="Body for PUT /users/{user_id} (admin).",
	),
	RegisteredSchema(
		name="UserAdminPatch",
		model=UserAdminPatch,
		group="users",
		description="Body for PATCH /users/{user_id} (admin).",
	),
	RegisteredSchema(
		name="UserResponse",
		model=UserResponse,
		group="users",
		description="User profile in API responses.",
	),
)
