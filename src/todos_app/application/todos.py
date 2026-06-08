from uuid import UUID

from todos_app.application.errors import TodoNotFoundError, TodoOwnerChangeForbiddenError
from todos_app.domain.auth.authorization import (
	is_update_owner_change_forbidden,
	list_owner_filter,
	resolve_create_owner_id,
)
from todos_app.domain.todos.entity import Todo
from todos_app.domain.todos.page import TodoPage
from todos_app.domain.todos.repository import TodoRepository


async def list_todos_for_actor(
	repo: TodoRepository,
	*,
	last_id: UUID | None,
	limit: int,
	actor_id: UUID,
	actor_role: str,
) -> TodoPage:
	owner_filter = list_owner_filter(actor_id=actor_id, actor_role=actor_role)
	return await repo.list_page(last_id, limit, owner_id=owner_filter)


async def create_todo_for_actor(
	repo: TodoRepository,
	todo: Todo,
	*,
	actor_id: UUID,
	actor_role: str,
	requested_owner_id: UUID | None,
) -> Todo:
	owner_id = resolve_create_owner_id(
		actor_id=actor_id,
		actor_role=actor_role,
		requested_owner_id=requested_owner_id,
	)
	entity = Todo(
		id=todo.id,
		title=todo.title,
		description=todo.description,
		priority=todo.priority,
		completed=todo.completed,
		owner_id=owner_id,
	)
	return await repo.add(entity)


async def get_todo_for_actor(
	repo: TodoRepository,
	todo_id: UUID,
	*,
	actor_id: UUID,
	actor_role: str,
) -> Todo:
	owner_filter = list_owner_filter(actor_id=actor_id, actor_role=actor_role)
	todo = await repo.get_by_id(todo_id, owner_id=owner_filter)
	if todo is None:
		raise TodoNotFoundError(actor_role=actor_role)
	return todo


async def update_todo_for_actor(
	repo: TodoRepository,
	todo_id: UUID,
	merged: Todo,
	*,
	actor_id: UUID,
	actor_role: str,
	requested_owner_id: UUID | None,
	existing_todo: Todo | None = None,
) -> Todo:
	if existing_todo is None:
		existing_todo = await get_todo_for_actor(
			repo,
			todo_id,
			actor_id=actor_id,
			actor_role=actor_role,
		)
	if is_update_owner_change_forbidden(
		actor_role=actor_role,
		existing_owner_id=existing_todo.owner_id,
		requested_owner_id=requested_owner_id,
	):
		raise TodoOwnerChangeForbiddenError
	owner_filter = list_owner_filter(actor_id=actor_id, actor_role=actor_role)
	updated_todo = await repo.update(merged, owner_id=owner_filter)
	if updated_todo is None:
		raise TodoNotFoundError(actor_role=actor_role)
	return updated_todo


async def delete_todo_for_actor(
	repo: TodoRepository,
	todo_id: UUID,
	*,
	actor_id: UUID,
	actor_role: str,
) -> None:
	await get_todo_for_actor(
		repo,
		todo_id,
		actor_id=actor_id,
		actor_role=actor_role,
	)
	owner_filter = list_owner_filter(actor_id=actor_id, actor_role=actor_role)
	deleted = await repo.delete(todo_id, owner_id=owner_filter)
	if not deleted:
		raise TodoNotFoundError(actor_role=actor_role)
