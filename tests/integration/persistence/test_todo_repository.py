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


async def _create_todo(
	db_session: AsyncSession,
	*,
	owner: User,
	title: str,
	description: str | None = None,
	priority: str | None = "low",
) -> Todo:
	assert owner.id is not None
	repo = SqlAlchemyTodoRepository(db_session)
	created = await repo.add(
		Todo(
			id=None,
			title=title,
			description=description,
			priority=priority,
			completed=False,
			owner_id=owner.id,
		)
	)
	await db_session.commit()
	assert created.id is not None
	return created


async def test_given_null_optional_fields_when_adding_todo_then_persists(
	db_session: AsyncSession,
) -> None:
	# given
	owner = await _create_user(db_session, username="owner-null-fields")
	repo = SqlAlchemyTodoRepository(db_session)
	assert owner.id is not None

	# when
	created = await repo.add(
		Todo(
			id=None,
			title="Title only",
			description=None,
			priority=None,
			completed=False,
			owner_id=owner.id,
		)
	)
	await db_session.commit()

	# then
	assert created.id is not None
	assert created.title == "Title only"
	assert created.description is None
	assert created.priority is None


async def test_given_persisted_todo_when_getting_by_id_then_returns_todo(
	db_session: AsyncSession,
) -> None:
	# given
	owner = await _create_user(db_session, username="owner-a")
	created = await _create_todo(
		db_session,
		owner=owner,
		title="Persisted",
		description="desc",
	)
	repo = SqlAlchemyTodoRepository(db_session)
	assert created.id is not None

	# when
	fetched = await repo.get_by_id(created.id)

	# then
	assert fetched is not None
	assert fetched.title == "Persisted"
	assert fetched.owner_id == owner.id


async def test_given_todos_for_multiple_owners_when_listing_with_owner_filter_then_returns_owner_items(
	db_session: AsyncSession,
) -> None:
	# given
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

	# when
	user_page = await repo.list_page(None, 10, owner_id=owner_a.id)

	# then
	assert [t.title for t in user_page.items] == ["A", "B"]


async def test_given_multiple_todos_when_listing_with_cursor_pagination_then_returns_pages(
	db_session: AsyncSession,
) -> None:
	# given
	owner_a = await _create_user(db_session, username="owner-cursor-a")
	owner_b = await _create_user(db_session, username="owner-cursor-b")
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

	# when
	first_page = await repo.list_page(None, 1, owner_id=None)
	second_page = await repo.list_page(first_page.next_last_id, 10, owner_id=None)

	# then
	assert len(first_page.items) == 1
	assert first_page.next_last_id is not None
	assert len(second_page.items) == 2


async def test_given_todo_owned_by_user_a_when_getting_with_owner_a_filter_then_returns_todo(
	db_session: AsyncSession,
) -> None:
	# given
	owner_a = await _create_user(db_session, username="owner-d")
	created = await _create_todo(db_session, owner=owner_a, title="Owned")
	repo = SqlAlchemyTodoRepository(db_session)
	assert owner_a.id is not None
	assert created.id is not None

	# when
	result = await repo.get_by_id(created.id, owner_id=owner_a.id)

	# then
	assert result is not None


async def test_given_todo_owned_by_user_a_when_getting_with_owner_b_filter_then_returns_none(
	db_session: AsyncSession,
) -> None:
	# given
	owner_a = await _create_user(db_session, username="owner-e2")
	owner_b = await _create_user(db_session, username="owner-e3")
	created = await _create_todo(db_session, owner=owner_a, title="Owned-other")
	repo = SqlAlchemyTodoRepository(db_session)
	assert owner_b.id is not None
	assert created.id is not None

	# when
	result = await repo.get_by_id(created.id, owner_id=owner_b.id)

	# then
	assert result is None


async def test_given_todo_owned_by_user_a_when_updating_with_owner_a_filter_then_persists(
	db_session: AsyncSession,
) -> None:
	# given
	owner_a = await _create_user(db_session, username="owner-f")
	created = await _create_todo(db_session, owner=owner_a, title="Original")
	repo = SqlAlchemyTodoRepository(db_session)
	assert owner_a.id is not None
	assert created.id is not None

	# when
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

	# then
	assert updated is not None
	assert updated.title == "Updated"


async def test_given_todo_owned_by_user_a_when_updating_with_owner_b_filter_then_returns_none(
	db_session: AsyncSession,
) -> None:
	# given
	owner_a = await _create_user(db_session, username="owner-g")
	owner_b = await _create_user(db_session, username="owner-g2")
	created = await _create_todo(db_session, owner=owner_a, title="Blocked-update")
	repo = SqlAlchemyTodoRepository(db_session)
	assert owner_a.id is not None
	assert owner_b.id is not None
	assert created.id is not None

	# when
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

	# then
	assert mismatch is None


async def test_given_todo_owned_by_user_a_when_deleting_with_owner_b_filter_then_returns_false(
	db_session: AsyncSession,
) -> None:
	# given
	owner_a = await _create_user(db_session, username="owner-h")
	owner_b = await _create_user(db_session, username="owner-i")
	created = await _create_todo(db_session, owner=owner_a, title="Delete me")
	repo = SqlAlchemyTodoRepository(db_session)
	assert owner_b.id is not None
	assert created.id is not None

	# when
	deleted = await repo.delete(created.id, owner_id=owner_b.id)

	# then
	assert deleted is False
	assert await repo.get_by_id(created.id) is not None


async def test_given_todo_owned_by_user_a_when_deleting_with_owner_a_filter_then_removes_todo(
	db_session: AsyncSession,
) -> None:
	# given
	owner_a = await _create_user(db_session, username="owner-h2")
	created = await _create_todo(db_session, owner=owner_a, title="Delete me for real")
	repo = SqlAlchemyTodoRepository(db_session)
	assert owner_a.id is not None
	assert created.id is not None

	# when
	deleted = await repo.delete(created.id, owner_id=owner_a.id)
	await db_session.commit()

	# then
	assert deleted is True
	assert await repo.get_by_id(created.id) is None
