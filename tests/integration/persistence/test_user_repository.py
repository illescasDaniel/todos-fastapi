import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from todos_app.domain.users.entity import User
from todos_app.infrastructure.persistence.users.repository import SqlAlchemyUserRepository


pytestmark = pytest.mark.integration


async def _add_user(db_session: AsyncSession, *, username: str = "jane") -> User:
	repo = SqlAlchemyUserRepository(db_session)
	created = await repo.add(
		User(
			id=None,
			email="jane@example.com",
			username=username,
			first_name="Jane",
			last_name="Doe",
			hashed_password="hashed",
			is_active=True,
			role="user",
		)
	)
	await db_session.commit()
	if created.id is None:
		raise RuntimeError("repository did not assign user id on insert")
	return created


async def test_given_new_user_entity_when_adding_to_repository_then_assigns_id(
	db_session: AsyncSession,
) -> None:
	# given
	repo = SqlAlchemyUserRepository(db_session)

	# when
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

	# then
	assert created.id is not None


async def test_given_persisted_user_when_getting_by_id_then_returns_user(
	db_session: AsyncSession,
) -> None:
	# given
	created = await _add_user(db_session)
	repo = SqlAlchemyUserRepository(db_session)
	assert created.id is not None

	# when
	by_id = await repo.get_by_id(created.id)

	# then
	assert by_id is not None
	assert by_id.email == "jane@example.com"


async def test_given_persisted_user_when_getting_by_username_then_returns_same_user(
	db_session: AsyncSession,
) -> None:
	# given
	created = await _add_user(db_session)
	repo = SqlAlchemyUserRepository(db_session)

	# when
	by_username = await repo.get_by_username("jane")

	# then
	assert by_username is not None
	assert by_username.id == created.id


async def test_given_persisted_user_when_updating_then_persists_changes(
	db_session: AsyncSession,
) -> None:
	# given
	created = await _add_user(db_session)
	repo = SqlAlchemyUserRepository(db_session)
	assert created.id is not None

	# when
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

	# then
	assert updated is not None
	assert updated.first_name == "Janet"
	refetched = await repo.get_by_id(created.id)
	assert refetched is not None
	assert refetched.first_name == "Janet"


async def test_given_user_with_todo_when_deleting_user_then_removes_user_and_todos(
	db_session: AsyncSession,
) -> None:
	# given
	from todos_app.domain.todos.entity import Todo
	from todos_app.infrastructure.persistence.todos.repository import SqlAlchemyTodoRepository

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

	# when
	deleted = await user_repo.delete(user.id)
	await db_session.commit()

	# then
	assert deleted is True
	assert await user_repo.get_by_id(user.id) is None
	assert await todo_repo.get_by_id(todo_id) is None
