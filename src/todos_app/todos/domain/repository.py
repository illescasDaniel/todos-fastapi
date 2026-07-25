from typing import Protocol
from uuid import UUID

from todos_app.todos.domain.entity import Todo
from todos_app.todos.domain.page import TodoPage


class TodoRepository(Protocol):
	async def list_page(self, last_id: UUID | None, limit: int, *, owner_id: UUID | None = None) -> TodoPage: ...

	async def get_by_id(self, todo_id: UUID, *, owner_id: UUID | None = None) -> Todo | None: ...

	async def add(self, todo: Todo) -> Todo: ...

	async def update(self, todo: Todo, *, owner_id: UUID | None = None) -> Todo | None: ...

	async def delete(self, todo_id: UUID, *, owner_id: UUID | None = None) -> bool: ...
