from typing import Any, cast
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from todos_app.domain.ids import new_id
from todos_app.domain.todos.entity import Todo
from todos_app.domain.todos.page import TodoPage
from todos_app.infrastructure.persistence.todos import mapper
from todos_app.infrastructure.persistence.todos.orm import TodoModel


class SqlAlchemyTodoRepository:
	def __init__(self, db: AsyncSession) -> None:
		self._db = db

	async def list_page(self, last_id: UUID | None, limit: int, *, owner_id: UUID | None = None) -> TodoPage:
		stmt = select(TodoModel).order_by(TodoModel.id).limit(limit + 1)
		if owner_id is not None:
			stmt = stmt.where(TodoModel.owner_id == owner_id)
		if last_id is not None:
			stmt = stmt.where(TodoModel.id > last_id)

		result = await self._db.execute(stmt)
		rows = result.scalars().all()
		has_more = len(rows) > limit
		page_rows = rows[:limit]
		items = mapper.to_entities(page_rows)
		next_last_id = page_rows[-1].id if has_more and page_rows else None
		return TodoPage(items=items, next_last_id=next_last_id)

	async def get_by_id(self, todo_id: UUID, *, owner_id: UUID | None = None) -> Todo | None:
		stmt = select(TodoModel).where(TodoModel.id == todo_id)
		if owner_id is not None:
			stmt = stmt.where(TodoModel.owner_id == owner_id)
		result = await self._db.execute(stmt)
		row = result.scalar_one_or_none()
		if row is None:
			return None
		return mapper.to_entity(row)

	async def add(self, todo: Todo) -> Todo:
		todo_id = todo.id if todo.id is not None else new_id()
		row = mapper.to_orm(todo, id=todo_id)
		self._db.add(row)
		await self._db.flush()
		return mapper.to_entity(row)

	async def update(self, todo: Todo, *, owner_id: UUID | None = None) -> Todo | None:
		if todo.id is None:
			return None
		stmt = update(TodoModel).where(TodoModel.id == todo.id)
		if owner_id is not None:
			stmt = stmt.where(TodoModel.owner_id == owner_id)
		stmt = stmt.values(
			title=todo.title,
			description=todo.description,
			priority=todo.priority,
			completed=todo.completed,
			owner_id=todo.owner_id,
		).returning(TodoModel)
		result = await self._db.execute(stmt)
		row = result.scalar_one_or_none()
		if row is None:
			return None
		return mapper.to_entity(row)

	async def delete(self, todo_id: UUID, *, owner_id: UUID | None = None) -> bool:
		stmt = delete(TodoModel).where(TodoModel.id == todo_id)
		if owner_id is not None:
			stmt = stmt.where(TodoModel.owner_id == owner_id)
		result = cast(CursorResult[Any], await self._db.execute(stmt))
		return result.rowcount > 0
