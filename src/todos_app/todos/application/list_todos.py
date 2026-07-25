from uuid import UUID

from todos_app.todos.domain.authorization import list_owner_filter
from todos_app.todos.domain.page import TodoPage
from todos_app.todos.domain.repository import TodoRepository


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
