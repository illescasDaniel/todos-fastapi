from collections.abc import Callable
from uuid import UUID

from todos_app.todos.application.errors import TodoNotFoundError, TodoOwnerChangeForbiddenError
from todos_app.todos.application.get_todo import get_todo_for_actor
from todos_app.todos.domain.authorization import (
	is_update_owner_change_forbidden,
	list_owner_filter,
	resolve_update_owner_id,
)
from todos_app.todos.domain.entity import Todo
from todos_app.todos.domain.repository import TodoRepository


async def update_todo_for_actor(
	repo: TodoRepository,
	todo_id: UUID,
	merge: Callable[[Todo, UUID], Todo],
	*,
	actor_id: UUID,
	actor_role: str,
	requested_owner_id: UUID | None,
) -> Todo:
	existing_todo = await get_todo_for_actor(
		repo,
		todo_id,
		actor_id=actor_id,
		actor_role=actor_role,
	)
	existing_owner_id = existing_todo.owner_id
	if existing_owner_id is None:
		raise TodoNotFoundError(actor_role=actor_role)
	if is_update_owner_change_forbidden(
		actor_role=actor_role,
		existing_owner_id=existing_owner_id,
		requested_owner_id=requested_owner_id,
	):
		raise TodoOwnerChangeForbiddenError
	owner_id = resolve_update_owner_id(
		existing_owner_id=existing_owner_id,
		requested_owner_id=requested_owner_id,
	)
	merged = merge(existing_todo, owner_id)
	owner_filter = list_owner_filter(actor_id=actor_id, actor_role=actor_role)
	updated_todo = await repo.update(merged, owner_id=owner_filter)
	if updated_todo is None:
		raise TodoNotFoundError(actor_role=actor_role)
	return updated_todo
