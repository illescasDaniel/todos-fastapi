import pytest

from factories import TEST_TODO_ID, TEST_USER_ID
from todos_app.domain.todos.entity import Todo
from todos_app.infrastructure.persistence.todos import mapper
from todos_app.infrastructure.persistence.todos.orm import TodoModel


pytestmark = pytest.mark.unit


def test_given_orm_with_null_optionals_when_mapping_to_entity_then_maps_nullable_fields() -> None:
	# given
	orm = TodoModel(
		id=TEST_TODO_ID,
		title="Task",
		description=None,
		priority=None,
		completed=False,
		owner_id=TEST_USER_ID,
	)

	# when
	entity = mapper.to_entity(orm)

	# then
	assert entity.title == "Task"
	assert entity.description is None
	assert entity.priority is None


def test_given_todo_entity_when_round_tripping_through_orm_then_preserves_fields() -> None:
	# given
	entity = Todo(
		id=TEST_TODO_ID,
		title="Task",
		description="Details",
		priority="high",
		completed=True,
		owner_id=TEST_USER_ID,
	)

	# when
	orm = mapper.to_orm(entity, id=TEST_TODO_ID)
	round_tripped = mapper.to_entity(orm)

	# then
	assert round_tripped == entity


def test_given_minimal_todo_entity_when_round_tripping_through_orm_then_preserves_null_optionals() -> None:
	# given
	entity = Todo(
		id=TEST_TODO_ID,
		title="Minimal",
		description=None,
		priority=None,
		completed=False,
		owner_id=TEST_USER_ID,
	)

	# when
	round_tripped = mapper.to_entity(mapper.to_orm(entity, id=TEST_TODO_ID))

	# then
	assert round_tripped == entity


def test_given_todo_without_owner_when_mapping_to_orm_then_raises() -> None:
	# given
	entity = Todo(
		id=TEST_TODO_ID,
		title="Draft",
		description=None,
		priority=None,
		completed=False,
		owner_id=None,
	)

	# when / then
	with pytest.raises(ValueError, match="owner_id must be set"):
		mapper.to_orm(entity, id=TEST_TODO_ID)
