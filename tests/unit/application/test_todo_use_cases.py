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


async def test_list_todos_for_actor_scopes_to_owner(repo: FakeTodoRepository) -> None:
	page = await todo_use_cases.list_todos_for_actor(
		repo,
		last_id=None,
		limit=10,
		actor_id=TEST_ACTOR_ID,
		actor_role="user",
	)
	assert len(page.items) == 1
	assert page.items[0].id == TEST_TODO_ID


async def test_list_todos_for_actor_returns_all_for_admin(repo: FakeTodoRepository) -> None:
	page = await todo_use_cases.list_todos_for_actor(
		repo,
		last_id=None,
		limit=10,
		actor_id=TEST_ADMIN_ID,
		actor_role=ADMIN_ROLE,
	)
	assert len(page.items) == 2


async def test_create_todo_for_actor_assigns_actor_as_owner(repo: FakeTodoRepository) -> None:
	entity = Todo(
		id=None,
		title="New",
		description=None,
		priority="low",
		completed=False,
		owner_id=TEST_ACTOR_ID_B,
	)
	created = await todo_use_cases.create_todo_for_actor(
		repo,
		entity,
		actor_id=TEST_ACTOR_ID,
		actor_role="user",
		requested_owner_id=TEST_ACTOR_ID_B,
	)
	assert created.owner_id == TEST_ACTOR_ID


async def test_create_todo_for_actor_allows_admin_requested_owner(repo: FakeTodoRepository) -> None:
	entity = Todo(
		id=None,
		title="Admin created",
		description=None,
		priority="low",
		completed=False,
		owner_id=TEST_ACTOR_ID,
	)
	created = await todo_use_cases.create_todo_for_actor(
		repo,
		entity,
		actor_id=TEST_ADMIN_ID,
		actor_role=ADMIN_ROLE,
		requested_owner_id=TEST_ACTOR_ID_B,
	)
	assert created.owner_id == TEST_ACTOR_ID_B


async def test_get_todo_for_actor_returns_owned_todo(repo: FakeTodoRepository) -> None:
	todo = await todo_use_cases.get_todo_for_actor(
		repo,
		TEST_TODO_ID,
		actor_id=TEST_ACTOR_ID,
		actor_role="user",
	)
	assert todo.id == TEST_TODO_ID
	assert todo.owner_id == TEST_ACTOR_ID


async def test_get_todo_for_actor_raises_when_out_of_scope(repo: FakeTodoRepository) -> None:
	with pytest.raises(TodoNotFoundError):
		await todo_use_cases.get_todo_for_actor(
			repo,
			TEST_TODO_ID_B,
			actor_id=TEST_ACTOR_ID,
			actor_role="user",
		)


async def test_update_todo_for_actor_forbids_owner_change(repo: FakeTodoRepository) -> None:
	merged = Todo(
		id=TEST_TODO_ID,
		title="Mine",
		description=None,
		priority="low",
		completed=False,
		owner_id=UNKNOWN_ID,
	)
	with pytest.raises(TodoOwnerChangeForbiddenError):
		await todo_use_cases.update_todo_for_actor(
			repo,
			TEST_TODO_ID,
			merged,
			actor_id=TEST_ACTOR_ID,
			actor_role="user",
			requested_owner_id=UNKNOWN_ID,
		)


async def test_delete_todo_for_actor_removes_todo(repo: FakeTodoRepository) -> None:
	await todo_use_cases.delete_todo_for_actor(
		repo,
		TEST_TODO_ID,
		actor_id=TEST_ACTOR_ID,
		actor_role="user",
	)
	assert await repo.get_by_id(TEST_TODO_ID) is None


async def test_update_todo_for_actor_refetches_when_existing_todo_is_none(repo: FakeTodoRepository) -> None:
	merged = Todo(
		id=TEST_TODO_ID,
		title="Updated",
		description=None,
		priority="low",
		completed=True,
		owner_id=TEST_ACTOR_ID,
	)
	updated = await todo_use_cases.update_todo_for_actor(
		repo,
		TEST_TODO_ID,
		merged,
		actor_id=TEST_ACTOR_ID,
		actor_role="user",
		requested_owner_id=None,
		existing_todo=None,
	)
	assert updated.title == "Updated"
	assert updated.completed is True


async def test_update_todo_for_actor_allows_admin_owner_change(repo: FakeTodoRepository) -> None:
	merged = Todo(
		id=TEST_TODO_ID,
		title="Mine",
		description=None,
		priority="low",
		completed=False,
		owner_id=TEST_ACTOR_ID_B,
	)
	updated = await todo_use_cases.update_todo_for_actor(
		repo,
		TEST_TODO_ID,
		merged,
		actor_id=TEST_ADMIN_ID,
		actor_role=ADMIN_ROLE,
		requested_owner_id=TEST_ACTOR_ID_B,
	)
	assert updated.owner_id == TEST_ACTOR_ID_B


async def test_update_todo_for_actor_raises_when_persist_returns_none(repo: FakeTodoRepository) -> None:
	merged = Todo(
		id=UNKNOWN_ID,
		title="Missing",
		description=None,
		priority="low",
		completed=False,
		owner_id=TEST_ACTOR_ID,
	)
	with pytest.raises(TodoNotFoundError):
		await todo_use_cases.update_todo_for_actor(
			repo,
			UNKNOWN_ID,
			merged,
			actor_id=TEST_ACTOR_ID,
			actor_role="user",
			requested_owner_id=None,
		)


async def test_delete_todo_for_actor_raises_when_delete_returns_false() -> None:
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
	with pytest.raises(TodoNotFoundError):
		await todo_use_cases.delete_todo_for_actor(
			repo,
			TEST_TODO_ID,
			actor_id=TEST_ACTOR_ID,
			actor_role="user",
		)
