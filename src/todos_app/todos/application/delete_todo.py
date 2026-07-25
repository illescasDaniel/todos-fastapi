from uuid import UUID

from todos_app.todos.application.errors import TodoNotFoundError
from todos_app.todos.application.get_todo import get_todo_for_actor
from todos_app.todos.domain.authorization import list_owner_filter
from todos_app.todos.domain.repository import TodoRepository


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
