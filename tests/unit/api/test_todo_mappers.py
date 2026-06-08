import pytest

from factories import TEST_ACTOR_ID, TEST_TODO_ID, TEST_TODO_ID_B, TEST_USER_ID
from todos_app.api.todos import mappers
from todos_app.api.todos.schemas import TodoCreate, TodoPatch, TodoUpdate
from todos_app.domain.todos.entity import Todo


pytestmark = pytest.mark.unit


def test_create_to_entity_maps_optional_null_fields() -> None:
	body = TodoCreate(title="Task only")
	entity = mappers.create_to_entity(body, owner_id=TEST_ACTOR_ID)
	assert entity.title == "Task only"
	assert entity.description is None
	assert entity.priority is None


def test_create_to_entity_maps_fields() -> None:
	body = TodoCreate(
		title="Task",
		description="Details",
		priority="high",
		completed=True,
	)
	entity = mappers.create_to_entity(body, owner_id=TEST_ACTOR_ID)
	assert entity.id is None
	assert entity.title == "Task"
	assert entity.description == "Details"
	assert entity.priority == "high"
	assert entity.completed is True
	assert entity.owner_id == TEST_ACTOR_ID


def test_to_response_maps_entity() -> None:
	todo = Todo(
		id=TEST_TODO_ID,
		title="Task",
		description="Details",
		priority="high",
		completed=False,
		owner_id=TEST_USER_ID,
	)
	response = mappers.to_response(todo)
	assert response.id == TEST_TODO_ID
	assert response.title == "Task"
	assert response.owner_id == TEST_USER_ID


def test_update_to_entity_maps_fields() -> None:
	body = TodoUpdate(
		title="Updated",
		description="New details",
		priority="low",
		completed=True,
	)
	entity = mappers.update_to_entity(body, todo_id=TEST_TODO_ID, owner_id=TEST_USER_ID)
	assert entity.id == TEST_TODO_ID
	assert entity.title == "Updated"
	assert entity.owner_id == TEST_USER_ID


def test_apply_todo_patch_clears_description() -> None:
	existing = Todo(
		id=TEST_TODO_ID,
		title="Task",
		description="Details",
		priority="high",
		completed=False,
		owner_id=TEST_USER_ID,
	)
	updated = mappers.apply_todo_patch(existing, {"description": None}, owner_id=TEST_USER_ID)
	assert updated.description is None
	assert updated.title == "Task"
	assert updated.priority == "high"


def test_patch_fields_includes_explicit_null_description() -> None:
	body = TodoPatch.model_validate({"description": None})
	fields = mappers.patch_fields(body)
	assert fields == {"description": None}


def test_apply_todo_patch_merges_fields() -> None:
	existing = Todo(
		id=TEST_TODO_ID,
		title="Task",
		description="Details",
		priority="high",
		completed=False,
		owner_id=TEST_USER_ID,
	)
	updated = mappers.apply_todo_patch(existing, {"title": "Patched", "completed": True}, owner_id=TEST_USER_ID)
	assert updated.title == "Patched"
	assert updated.completed is True
	assert updated.description == "Details"


def test_patch_fields_excludes_unset() -> None:
	body = TodoPatch(title="Patched")
	fields = mappers.patch_fields(body)
	assert fields == {"title": "Patched"}


def test_to_response_list_maps_entities() -> None:
	todos = [
		Todo(
			id=TEST_TODO_ID,
			title="A",
			description=None,
			priority="low",
			completed=False,
			owner_id=TEST_USER_ID,
		),
		Todo(
			id=TEST_TODO_ID_B,
			title="B",
			description=None,
			priority="low",
			completed=False,
			owner_id=TEST_USER_ID,
		),
	]
	responses = mappers.to_response_list(todos)
	assert len(responses) == 2
	assert responses[0].title == "A"
	assert responses[1].title == "B"
