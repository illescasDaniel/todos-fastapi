import pytest

from factories import TEST_TODO_ID, TEST_TODO_ID_B, TEST_USER_ID
from todos_app.api.todos import mappers
from todos_app.api.todos.schemas import TodoCreate, TodoPatch, TodoUpdate
from todos_app.domain.todos.entity import Todo


pytestmark = pytest.mark.unit


def test_given_minimal_create_body_when_mapping_to_entity_then_maps_null_optionals() -> None:
	# given
	body = TodoCreate(title="Task only")

	# when
	entity = mappers.create_to_entity(body)

	# then
	assert entity.title == "Task only"
	assert entity.description is None
	assert entity.priority is None
	assert entity.owner_id is None


def test_given_full_create_body_when_mapping_to_entity_then_maps_all_fields() -> None:
	# given
	body = TodoCreate(
		title="Task",
		description="Details",
		priority="high",
		completed=True,
	)

	# when
	entity = mappers.create_to_entity(body)

	# then
	assert entity.id is None
	assert entity.title == "Task"
	assert entity.description == "Details"
	assert entity.priority == "high"
	assert entity.completed is True
	assert entity.owner_id is None


def test_given_todo_entity_when_mapping_to_response_then_maps_fields() -> None:
	# given
	todo = Todo(
		id=TEST_TODO_ID,
		title="Task",
		description="Details",
		priority="high",
		completed=False,
		owner_id=TEST_USER_ID,
	)

	# when
	response = mappers.to_response(todo)

	# then
	assert response.id == TEST_TODO_ID
	assert response.title == "Task"
	assert response.owner_id == TEST_USER_ID


def test_given_update_body_when_mapping_to_entity_then_maps_fields() -> None:
	# given
	body = TodoUpdate(
		title="Updated",
		description="New details",
		priority="low",
		completed=True,
	)

	# when
	entity = mappers.update_to_entity(body, todo_id=TEST_TODO_ID, owner_id=TEST_USER_ID)

	# then
	assert entity.id == TEST_TODO_ID
	assert entity.title == "Updated"
	assert entity.owner_id == TEST_USER_ID


def test_given_null_description_patch_when_applying_to_todo_then_clears_description() -> None:
	# given
	existing = Todo(
		id=TEST_TODO_ID,
		title="Task",
		description="Details",
		priority="high",
		completed=False,
		owner_id=TEST_USER_ID,
	)

	# when
	updated = mappers.apply_todo_patch(existing, {"description": None}, owner_id=TEST_USER_ID)

	# then
	assert updated.description is None
	assert updated.title == "Task"
	assert updated.priority == "high"


def test_given_explicit_null_description_when_extracting_patch_fields_then_includes_null() -> None:
	# given

	# when
	body = TodoPatch.model_validate({"description": None})
	fields = mappers.patch_fields(body)

	# then
	assert fields == {"description": None}


def test_given_partial_patch_fields_when_applying_to_todo_then_merges_fields() -> None:
	# given
	existing = Todo(
		id=TEST_TODO_ID,
		title="Task",
		description="Details",
		priority="high",
		completed=False,
		owner_id=TEST_USER_ID,
	)

	# when
	updated = mappers.apply_todo_patch(
		existing,
		{"title": "Patched", "completed": True},
		owner_id=TEST_USER_ID,
	)

	# then
	assert updated.title == "Patched"
	assert updated.completed is True
	assert updated.description == "Details"


def test_given_partial_patch_body_when_extracting_patch_fields_then_excludes_unset() -> None:
	# given
	body = TodoPatch(title="Patched")

	# when
	fields = mappers.patch_fields(body)

	# then
	assert fields == {"title": "Patched"}


def test_given_todo_list_when_mapping_to_responses_then_maps_all_entities() -> None:
	# given
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

	# when
	responses = mappers.to_response_list(todos)

	# then
	assert len(responses) == 2
	assert responses[0].title == "A"
	assert responses[1].title == "B"
