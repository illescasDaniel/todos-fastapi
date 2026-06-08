from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from todos_app.domain.ids import JANE_USER_ID, SEED_TODO_IDS
from todos_app.domain.todos.field_limits import (
	DESCRIPTION_MAX_LENGTH,
	PRIORITY_MAX_LENGTH,
	TITLE_MAX_LENGTH,
)


def _reject_empty_string(value: object) -> object:
	if value == "":
		raise ValueError("must not be empty")
	return value


class TodoWriteBase(BaseModel):
	title: str = Field(min_length=1, max_length=TITLE_MAX_LENGTH)
	description: str | None = Field(default=None, max_length=DESCRIPTION_MAX_LENGTH)
	priority: str | None = Field(default=None, max_length=PRIORITY_MAX_LENGTH)
	completed: bool = False

	@field_validator("title", mode="before")
	@classmethod
	def validate_title(cls, value: object) -> object:
		if value is None:
			raise ValueError("title is required")
		return _reject_empty_string(value)

	@field_validator("description", "priority", mode="before")
	@classmethod
	def validate_optional_strings(cls, value: object) -> object:
		return _reject_empty_string(value)


class TodoCreate(TodoWriteBase):
	model_config = ConfigDict(
		extra="forbid",
		json_schema_extra={
			"examples": [
				{
					"title": "Set up FastAPI project",
					"description": "Initialize app, routes, and database wiring.",
					"priority": "high",
					"completed": False,
				}
			]
		},
	)

	owner_id: UUID | None = Field(
		default=None,
		description="Admin only: assign todo to another user.",
	)


class TodoPatch(BaseModel):
	model_config = ConfigDict(extra="forbid")

	title: str | None = Field(default=None, min_length=1, max_length=TITLE_MAX_LENGTH)
	description: str | None = Field(default=None, max_length=DESCRIPTION_MAX_LENGTH)
	priority: str | None = Field(default=None, max_length=PRIORITY_MAX_LENGTH)
	completed: bool | None = None
	owner_id: UUID | None = Field(
		default=None,
		description="Admins may reassign; non-admins get 403 if this differs from the existing owner.",
	)

	@model_validator(mode="after")
	def validate_patch_fields(self) -> "TodoPatch":
		if "title" in self.model_fields_set:
			if self.title is None:
				raise ValueError("title cannot be null")
			if self.title == "":
				raise ValueError("title must not be empty")
		for name in ("description", "priority"):
			if name in self.model_fields_set and getattr(self, name) == "":
				raise ValueError("must not be empty")
		return self


class TodoUpdate(TodoWriteBase):
	model_config = ConfigDict(
		extra="forbid",
		json_schema_extra={
			"examples": [
				{
					"title": "Set up FastAPI project",
					"description": "Routes, schemas, and repository wiring done.",
					"priority": "medium",
					"completed": True,
				}
			]
		},
	)

	owner_id: UUID | None = Field(
		default=None,
		description=(
			"Omit to keep the current owner. Admins may reassign; "
			"non-admins get 403 if this differs from the existing owner."
		),
	)


class TodoResponse(BaseModel):
	model_config = ConfigDict(
		from_attributes=True,
		json_schema_extra={
			"examples": [
				{
					"id": str(SEED_TODO_IDS[0]),
					"title": "Set up FastAPI project",
					"description": "Initialize app, routes, and database wiring.",
					"priority": "high",
					"completed": True,
					"owner_id": str(JANE_USER_ID),
				}
			]
		},
	)

	id: UUID
	title: str = Field(min_length=1, max_length=TITLE_MAX_LENGTH)
	description: str | None = Field(default=None, max_length=DESCRIPTION_MAX_LENGTH)
	priority: str | None = Field(default=None, max_length=PRIORITY_MAX_LENGTH)
	completed: bool
	owner_id: UUID


class TodoListResponse(BaseModel):
	model_config = ConfigDict(
		json_schema_extra={
			"examples": [
				{
					"items": [
						{
							"id": str(SEED_TODO_IDS[0]),
							"title": "Set up FastAPI project",
							"description": "Initialize app, routes, and database wiring.",
							"priority": "high",
							"completed": True,
							"owner_id": str(JANE_USER_ID),
						}
					],
					"next_last_id": str(SEED_TODO_IDS[2]),
					"limit": 20,
				}
			]
		},
	)

	items: list[TodoResponse]
	next_last_id: UUID | None
	limit: int
