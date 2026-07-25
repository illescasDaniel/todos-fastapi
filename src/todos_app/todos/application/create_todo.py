from uuid import UUID

from todos_app.todos.domain.authorization import resolve_create_owner_id
from todos_app.todos.domain.entity import Todo
from todos_app.todos.domain.repository import TodoRepository


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
