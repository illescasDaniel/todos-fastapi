from uuid import UUID

from todos_app.todos.application.errors import TodoNotFoundError
from todos_app.todos.domain.authorization import list_owner_filter
from todos_app.todos.domain.entity import Todo
from todos_app.todos.domain.repository import TodoRepository


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
