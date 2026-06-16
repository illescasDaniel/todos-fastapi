from uuid import UUID

import pytest

from factories import TEST_ACTOR_ID, TEST_ACTOR_ID_B, TEST_ADMIN_ID, TEST_TODO_ID, TEST_TODO_ID_B
from fakes.todo_repository import FakeTodoRepository
from todos_app.application import todos as todo_use_cases
from todos_app.application.errors import TodoNotFoundError, TodoOwnerChangeForbiddenError
from todos_app.domain.auth.authorization import ADMIN_ROLE
from todos_app.domain.ids import UNKNOWN_ID
from todos_app.domain.todos.entity import Todo


pytestmark = pytest.mark.unit


@pytest.fixture
def repo() -> FakeTodoRepository:
	return FakeTodoRepository(
		[
			Todo(
				id=TEST_TODO_ID,
				title="Mine",
				description=None,
				priority="low",
				completed=False,
				owner_id=TEST_ACTOR_ID,
			),
			Todo(
				id=TEST_TODO_ID_B,
				title="Theirs",
				description=None,
				priority="low",
				completed=False,
				owner_id=TEST_ACTOR_ID_B,
			),
		]
	)


async def test_given_regular_user_actor_when_listing_todos_then_scopes_to_owner(
	repo: FakeTodoRepository,
) -> None:
	# given
	actor_id = TEST_ACTOR_ID
	actor_role = "user"

	# when
	page = await todo_use_cases.list_todos_for_actor(
		repo,
		last_id=None,
		limit=10,
		actor_id=actor_id,
		actor_role=actor_role,
	)

	# then
	assert len(page.items) == 1
	assert page.items[0].id == TEST_TODO_ID


async def test_given_admin_actor_when_listing_todos_then_returns_all(
	repo: FakeTodoRepository,
) -> None:
	# given
	actor_id = TEST_ADMIN_ID
	actor_role = ADMIN_ROLE

	# when
	page = await todo_use_cases.list_todos_for_actor(
		repo,
		last_id=None,
		limit=10,
		actor_id=actor_id,
		actor_role=actor_role,
	)

	# then
	assert len(page.items) == 2


async def test_given_regular_user_creating_todo_when_assigning_owner_then_uses_actor_as_owner(
	repo: FakeTodoRepository,
) -> None:
	# given
	entity = Todo(
		id=None,
		title="New",
		description=None,
		priority="low",
		completed=False,
		owner_id=TEST_ACTOR_ID_B,
	)

	# when
	created = await todo_use_cases.create_todo_for_actor(
		repo,
		entity,
		actor_id=TEST_ACTOR_ID,
		actor_role="user",
		requested_owner_id=TEST_ACTOR_ID_B,
	)

	# then
	assert created.owner_id == TEST_ACTOR_ID


async def test_given_admin_creating_todo_when_requesting_owner_then_uses_requested_owner(
	repo: FakeTodoRepository,
) -> None:
	# given
	entity = Todo(
		id=None,
		title="Admin created",
		description=None,
		priority="low",
		completed=False,
		owner_id=TEST_ACTOR_ID,
	)

	# when
	created = await todo_use_cases.create_todo_for_actor(
		repo,
		entity,
		actor_id=TEST_ADMIN_ID,
		actor_role=ADMIN_ROLE,
		requested_owner_id=TEST_ACTOR_ID_B,
	)

	# then
	assert created.owner_id == TEST_ACTOR_ID_B


async def test_given_owned_todo_when_getting_for_regular_user_then_returns_todo(
	repo: FakeTodoRepository,
) -> None:
	# given
	todo_id = TEST_TODO_ID
	actor_id = TEST_ACTOR_ID
	actor_role = "user"

	# when
	todo = await todo_use_cases.get_todo_for_actor(
		repo,
		todo_id,
		actor_id=actor_id,
		actor_role=actor_role,
	)

	# then
	assert todo.id == TEST_TODO_ID
	assert todo.owner_id == TEST_ACTOR_ID


async def test_given_other_users_todo_when_getting_for_regular_user_then_raises_not_found(
	repo: FakeTodoRepository,
) -> None:
	# given
	todo_id = TEST_TODO_ID_B
	actor_id = TEST_ACTOR_ID
	actor_role = "user"

	# when
	with pytest.raises(TodoNotFoundError):
		await todo_use_cases.get_todo_for_actor(
			repo,
			todo_id,
			actor_id=actor_id,
			actor_role=actor_role,
		)

	# then


async def test_given_regular_user_changing_owner_when_updating_todo_then_raises_forbidden(
	repo: FakeTodoRepository,
) -> None:
	# given
	def merge(_existing: Todo, owner_id: UUID) -> Todo:
		return Todo(
			id=TEST_TODO_ID,
			title="Mine",
			description=None,
			priority="low",
			completed=False,
			owner_id=owner_id,
		)

	# when
	with pytest.raises(TodoOwnerChangeForbiddenError):
		await todo_use_cases.update_todo_for_actor(
			repo,
			TEST_TODO_ID,
			merge,
			actor_id=TEST_ACTOR_ID,
			actor_role="user",
			requested_owner_id=UNKNOWN_ID,
		)

	# then


async def test_given_owned_todo_when_deleting_for_regular_user_then_removes_todo(
	repo: FakeTodoRepository,
) -> None:
	# given
	todo_id = TEST_TODO_ID

	# when
	await todo_use_cases.delete_todo_for_actor(
		repo,
		todo_id,
		actor_id=TEST_ACTOR_ID,
		actor_role="user",
	)

	# then
	assert await repo.get_by_id(TEST_TODO_ID) is None


async def test_given_missing_existing_todo_when_updating_then_refetches_and_persists(
	repo: FakeTodoRepository,
) -> None:
	# given
	def merge(_existing: Todo, owner_id: UUID) -> Todo:
		return Todo(
			id=TEST_TODO_ID,
			title="Updated",
			description=None,
			priority="low",
			completed=True,
			owner_id=owner_id,
		)

	# when
	updated = await todo_use_cases.update_todo_for_actor(
		repo,
		TEST_TODO_ID,
		merge,
		actor_id=TEST_ACTOR_ID,
		actor_role="user",
		requested_owner_id=None,
	)

	# then
	assert updated.title == "Updated"
	assert updated.completed is True


async def test_given_admin_changing_owner_when_updating_todo_then_persists_new_owner(
	repo: FakeTodoRepository,
) -> None:
	# given
	def merge(_existing: Todo, owner_id: UUID) -> Todo:
		return Todo(
			id=TEST_TODO_ID,
			title="Mine",
			description=None,
			priority="low",
			completed=False,
			owner_id=owner_id,
		)

	# when
	updated = await todo_use_cases.update_todo_for_actor(
		repo,
		TEST_TODO_ID,
		merge,
		actor_id=TEST_ADMIN_ID,
		actor_role=ADMIN_ROLE,
		requested_owner_id=TEST_ACTOR_ID_B,
	)

	# then
	assert updated.owner_id == TEST_ACTOR_ID_B


async def test_given_unknown_todo_id_when_updating_then_raises_not_found(
	repo: FakeTodoRepository,
) -> None:
	# given
	def merge(_existing: Todo, owner_id: UUID) -> Todo:
		return Todo(
			id=UNKNOWN_ID,
			title="Missing",
			description=None,
			priority="low",
			completed=False,
			owner_id=owner_id,
		)

	# when
	with pytest.raises(TodoNotFoundError):
		await todo_use_cases.update_todo_for_actor(
			repo,
			UNKNOWN_ID,
			merge,
			actor_id=TEST_ACTOR_ID,
			actor_role="user",
			requested_owner_id=None,
		)

	# then


async def test_given_delete_returns_false_when_deleting_todo_then_raises_not_found() -> None:
	# given
	class DeleteFailsRepository(FakeTodoRepository):
		async def delete(self, todo_id: object, *, owner_id: object = None) -> bool:
			return False

	repo = DeleteFailsRepository(
		[
			Todo(
				id=TEST_TODO_ID,
				title="Mine",
				description=None,
				priority="low",
				completed=False,
				owner_id=TEST_ACTOR_ID,
			),
		]
	)

	# when
	with pytest.raises(TodoNotFoundError):
		await todo_use_cases.delete_todo_for_actor(
			repo,
			TEST_TODO_ID,
			actor_id=TEST_ACTOR_ID,
			actor_role="user",
		)

	# then
