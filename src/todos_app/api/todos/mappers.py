from typing import Any
from uuid import UUID

from todos_app.api.todos.schemas import TodoCreate, TodoPatch, TodoResponse, TodoUpdate
from todos_app.domain.todos.entity import Todo


def to_response(todo: Todo) -> TodoResponse:
	return TodoResponse.model_validate(todo)


def create_to_entity(todo: TodoCreate, owner_id: UUID) -> Todo:
	return Todo(
		id=None,
		title=todo.title,
		description=todo.description,
		priority=todo.priority,
		completed=todo.completed,
		owner_id=owner_id,
	)


def update_to_entity(todo: TodoUpdate, todo_id: UUID, owner_id: UUID) -> Todo:
	return Todo(
		id=todo_id,
		title=todo.title,
		description=todo.description,
		priority=todo.priority,
		completed=todo.completed,
		owner_id=owner_id,
	)


def apply_todo_patch(existing: Todo, fields: dict[str, Any], owner_id: UUID) -> Todo:
	if existing.id is None:
		raise ValueError("existing todo must have an id")
	return Todo(
		id=existing.id,
		title=fields.get("title", existing.title),
		description=fields.get("description", existing.description),
		priority=fields.get("priority", existing.priority),
		completed=fields.get("completed", existing.completed),
		owner_id=owner_id,
	)


def patch_fields(body: TodoPatch) -> dict[str, Any]:
	return body.model_dump(exclude_unset=True)


def to_response_list(todos: list[Todo]) -> list[TodoResponse]:
	return [TodoResponse.model_validate(todo) for todo in todos]
