import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from todos_app.domain.todos.entity import Todo
from todos_app.domain.users.entity import User
from todos_app.infrastructure.persistence.todos.repository import SqlAlchemyTodoRepository
from todos_app.infrastructure.persistence.users.repository import SqlAlchemyUserRepository


pytestmark = pytest.mark.integration


async def test_add_get_by_id_and_get_by_username(db_session: AsyncSession) -> None:
	repo = SqlAlchemyUserRepository(db_session)
	created = await repo.add(
		User(
			id=None,
			email="jane@example.com",
			username="jane",
			first_name="Jane",
			last_name="Doe",
			hashed_password="hashed",
			is_active=True,
			role="user",
		)
	)
	await db_session.commit()

	assert created.id is not None
	by_id = await repo.get_by_id(created.id)
	by_username = await repo.get_by_username("jane")
	assert by_id is not None
	assert by_username is not None
	assert by_id.email == "jane@example.com"
	assert by_username.id == created.id


async def test_update_persists_changes(db_session: AsyncSession) -> None:
	repo = SqlAlchemyUserRepository(db_session)
	created = await repo.add(
		User(
			id=None,
			email="jane@example.com",
			username="jane",
			first_name="Jane",
			last_name="Doe",
			hashed_password="hashed",
			is_active=True,
			role="user",
		)
	)
	await db_session.commit()

	assert created.id is not None
	updated = await repo.update(
		User(
			id=created.id,
			email=created.email,
			username=created.username,
			first_name="Janet",
			last_name=created.last_name,
			hashed_password=created.hashed_password,
			is_active=created.is_active,
			role=created.role,
		)
	)
	await db_session.commit()

	assert updated is not None
	assert updated.first_name == "Janet"
	refetched = await repo.get_by_id(created.id)
	assert refetched is not None
	assert refetched.first_name == "Janet"


async def test_delete_removes_user_and_their_todos(db_session: AsyncSession) -> None:
	user_repo = SqlAlchemyUserRepository(db_session)
	todo_repo = SqlAlchemyTodoRepository(db_session)
	user = await user_repo.add(
		User(
			id=None,
			email="delete@example.com",
			username="delete-me",
			first_name="Delete",
			last_name="Me",
			hashed_password="hashed",
			is_active=True,
			role="user",
		)
	)
	await db_session.commit()
	assert user.id is not None

	await todo_repo.add(
		Todo(
			id=None,
			title="Owned",
			description=None,
			priority="low",
			completed=False,
			owner_id=user.id,
		)
	)
	await db_session.commit()
	created_todo = await todo_repo.list_page(None, 10, owner_id=user.id)
	assert created_todo.items[0].id is not None
	todo_id = created_todo.items[0].id

	deleted = await user_repo.delete(user.id)
	await db_session.commit()
	assert deleted is True
	assert await user_repo.get_by_id(user.id) is None
	assert await todo_repo.get_by_id(todo_id) is None
