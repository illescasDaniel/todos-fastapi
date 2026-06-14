from typing import Any, cast
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from todos_app.domain.ids import new_id
from todos_app.domain.users.entity import User
from todos_app.infrastructure.persistence.todos.orm import TodoModel
from todos_app.infrastructure.persistence.users import mapper
from todos_app.infrastructure.persistence.users.orm import UserModel


class SqlAlchemyUserRepository:
	def __init__(self, db: AsyncSession) -> None:
		self._db = db

	async def add(self, user: User) -> User:
		user_id = user.id if user.id is not None else new_id()
		normalized = User(
			id=user.id,
			email=user.email,
			username=user.username.lower(),
			first_name=user.first_name,
			last_name=user.last_name,
			hashed_password=user.hashed_password,
			is_active=user.is_active,
			role=user.role,
			token_version=user.token_version,
		)
		row = mapper.to_orm(normalized, id=user_id)
		self._db.add(row)
		await self._db.flush()
		return mapper.to_entity(row)

	async def get_by_id(self, user_id: UUID) -> User | None:
		stmt = select(UserModel).where(UserModel.id == user_id)
		result = await self._db.execute(stmt)
		row = result.scalar_one_or_none()
		if row is None:
			return None
		return mapper.to_entity(row)

	async def get_by_username(self, username: str) -> User | None:
		stmt = select(UserModel).where(func.lower(UserModel.username) == username.lower())
		result = await self._db.execute(stmt)
		row = result.scalar_one_or_none()
		if row is None:
			return None
		return mapper.to_entity(row)

	async def update(self, user: User) -> User | None:
		if user.id is None:
			return None
		stmt = (
			update(UserModel)
			.where(UserModel.id == user.id)
			.values(
				email=user.email,
				username=user.username.lower(),
				first_name=user.first_name,
				last_name=user.last_name,
				hashed_password=user.hashed_password,
				is_active=user.is_active,
				role=user.role,
				token_version=user.token_version,
			)
			.returning(UserModel)
		)
		result = await self._db.execute(stmt)
		row = result.scalar_one_or_none()
		if row is None:
			return None
		return mapper.to_entity(row)

	async def delete(self, user_id: UUID) -> bool:
		await self._db.execute(delete(TodoModel).where(TodoModel.owner_id == user_id))
		result = cast(
			CursorResult[Any],
			await self._db.execute(delete(UserModel).where(UserModel.id == user_id)),
		)
		return result.rowcount > 0

	async def count_active_admins(self) -> int:
		stmt = select(func.count()).where(UserModel.role == "admin", UserModel.is_active.is_(True))
		result = await self._db.execute(stmt)
		return result.scalar_one()
