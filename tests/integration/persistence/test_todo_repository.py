import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from todos_app.domain.todos.entity import Todo
from todos_app.domain.users.entity import User
from todos_app.infrastructure.persistence.todos.repository import SqlAlchemyTodoRepository
from todos_app.infrastructure.persistence.users.repository import SqlAlchemyUserRepository


pytestmark = pytest.mark.integration


async def _create_user(db_session: AsyncSession, *, username: str) -> User:
	repo = SqlAlchemyUserRepository(db_session)
	user = await repo.add(
		User(
			id=None,
			email=f"{username}@example.com",
			username=username,
			first_name="Test",
			last_name="User",
			hashed_password="hashed",
			is_active=True,
			role="user",
		)
	)
	await db_session.commit()
	assert user.id is not None
	return user


async def test_add_and_get_by_id_persists_null_optional_fields(db_session: AsyncSession) -> None:
	owner = await _create_user(db_session, username="owner-null-fields")
	repo = SqlAlchemyTodoRepository(db_session)
	created = await repo.add(
		Todo(
			id=None,
			title="Title only",
			description=None,
			priority=None,
			completed=False,
			owner_id=owner.id,  # type: ignore[arg-type]
		)
	)
	await db_session.commit()

	assert created.id is not None
	fetched = await repo.get_by_id(created.id)
	assert fetched is not None
	assert fetched.title == "Title only"
	assert fetched.description is None
	assert fetched.priority is None


async def test_add_and_get_by_id(db_session: AsyncSession) -> None:
	owner = await _create_user(db_session, username="owner-a")
	repo = SqlAlchemyTodoRepository(db_session)
	created = await repo.add(
		Todo(
			id=None,
			title="Persisted",
			description="desc",
			priority="low",
			completed=False,
			owner_id=owner.id,  # type: ignore[arg-type]
		)
	)
	await db_session.commit()

	assert created.id is not None
	fetched = await repo.get_by_id(created.id)
	assert fetched is not None
	assert fetched.title == "Persisted"
	assert fetched.owner_id == owner.id


async def test_list_page_cursor_and_owner_filter(db_session: AsyncSession) -> None:
	owner_a = await _create_user(db_session, username="owner-b")
	owner_b = await _create_user(db_session, username="owner-c")
	assert owner_a.id is not None
	assert owner_b.id is not None

	repo = SqlAlchemyTodoRepository(db_session)
	for owner_id, title in ((owner_a.id, "A"), (owner_a.id, "B"), (owner_b.id, "C")):
		await repo.add(
			Todo(
				id=None,
				title=title,
				description=None,
				priority="low",
				completed=False,
				owner_id=owner_id,
			)
		)
	await db_session.commit()

	user_page = await repo.list_page(None, 10, owner_id=owner_a.id)
	assert [t.title for t in user_page.items] == ["A", "B"]

	first_page = await repo.list_page(None, 1, owner_id=None)
	assert len(first_page.items) == 1
	assert first_page.next_last_id is not None

	second_page = await repo.list_page(first_page.next_last_id, 10, owner_id=None)
	assert len(second_page.items) == 2


async def test_get_by_id_respects_owner_filter(db_session: AsyncSession) -> None:
	owner_a = await _create_user(db_session, username="owner-d")
	owner_b = await _create_user(db_session, username="owner-e")
	assert owner_a.id is not None
	assert owner_b.id is not None

	repo = SqlAlchemyTodoRepository(db_session)
	created = await repo.add(
		Todo(
			id=None,
			title="Owned",
			description=None,
			priority="low",
			completed=False,
			owner_id=owner_a.id,
		)
	)
	await db_session.commit()
	assert created.id is not None

	assert await repo.get_by_id(created.id, owner_id=owner_a.id) is not None
	assert await repo.get_by_id(created.id, owner_id=owner_b.id) is None


async def test_update_with_and_without_owner_filter(db_session: AsyncSession) -> None:
	owner_a = await _create_user(db_session, username="owner-f")
	owner_b = await _create_user(db_session, username="owner-g")
	assert owner_a.id is not None
	assert owner_b.id is not None

	repo = SqlAlchemyTodoRepository(db_session)
	created = await repo.add(
		Todo(
			id=None,
			title="Original",
			description=None,
			priority="low",
			completed=False,
			owner_id=owner_a.id,
		)
	)
	await db_session.commit()
	assert created.id is not None

	updated = await repo.update(
		Todo(
			id=created.id,
			title="Updated",
			description=None,
			priority="low",
			completed=True,
			owner_id=owner_a.id,
		),
		owner_id=owner_a.id,
	)
	await db_session.commit()
	assert updated is not None
	assert updated.title == "Updated"

	mismatch = await repo.update(
		Todo(
			id=created.id,
			title="Blocked",
			description=None,
			priority="low",
			completed=False,
			owner_id=owner_a.id,
		),
		owner_id=owner_b.id,
	)
	assert mismatch is None


async def test_delete_with_and_without_owner_filter(db_session: AsyncSession) -> None:
	owner_a = await _create_user(db_session, username="owner-h")
	owner_b = await _create_user(db_session, username="owner-i")
	assert owner_a.id is not None
	assert owner_b.id is not None

	repo = SqlAlchemyTodoRepository(db_session)
	created = await repo.add(
		Todo(
			id=None,
			title="Delete me",
			description=None,
			priority="low",
			completed=False,
			owner_id=owner_a.id,
		)
	)
	await db_session.commit()
	assert created.id is not None

	assert await repo.delete(created.id, owner_id=owner_b.id) is False
	assert await repo.get_by_id(created.id) is not None

	assert await repo.delete(created.id, owner_id=owner_a.id) is True
	await db_session.commit()
	assert await repo.get_by_id(created.id) is None
