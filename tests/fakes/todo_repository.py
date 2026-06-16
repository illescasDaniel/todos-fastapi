from uuid import UUID

from todos_app.domain.ids import new_id
from todos_app.domain.todos.entity import Todo
from todos_app.domain.todos.page import TodoPage


class FakeTodoRepository:
	def __init__(self, todos: list[Todo] | None = None) -> None:
		self._todos: dict[UUID, Todo] = {}
		if todos:
			for todo in todos:
				if todo.id is not None:
					self._todos[todo.id] = todo

	async def list_page(
		self,
		last_id: UUID | None,
		limit: int,
		*,
		owner_id: UUID | None = None,
	) -> TodoPage:
		todo_ids = sorted(self._todos)
		if last_id is not None:
			todo_ids = [todo_id for todo_id in todo_ids if todo_id > last_id]

		items: list[Todo] = []
		for todo_id in todo_ids:
			todo = self._todos[todo_id]
			if owner_id is not None and todo.owner_id != owner_id:
				continue
			items.append(todo)

		has_more = len(items) > limit
		page_items = items[:limit]
		next_last_id = page_items[-1].id if has_more and page_items else None
		return TodoPage(items=page_items, next_last_id=next_last_id)

	async def get_by_id(self, todo_id: UUID, *, owner_id: UUID | None = None) -> Todo | None:
		todo = self._todos.get(todo_id)
		if todo is None:
			return None
		if owner_id is not None and todo.owner_id != owner_id:
			return None
		return todo

	async def add(self, todo: Todo) -> Todo:
		new_todo_id = new_id()
		if todo.owner_id is None:
			raise ValueError("todo owner_id must be set before persist")
		stored = Todo(
			id=new_todo_id,
			title=todo.title,
			description=todo.description,
			priority=todo.priority,
			completed=todo.completed,
			owner_id=todo.owner_id,
		)
		self._todos[new_todo_id] = stored
		return stored

	async def update(self, todo: Todo, *, owner_id: UUID | None = None) -> Todo | None:
		if todo.id is None:
			return None
		existing = await self.get_by_id(todo.id, owner_id=owner_id)
		if existing is None:
			return None
		self._todos[todo.id] = todo
		return todo

	async def delete(self, todo_id: UUID, *, owner_id: UUID | None = None) -> bool:
		existing = await self.get_by_id(todo_id, owner_id=owner_id)
		if existing is None:
			return False
		del self._todos[todo_id]
		return True
