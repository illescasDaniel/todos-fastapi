import pytest

from factories import TEST_TODO_ID, TEST_USER_ID
from todos_app.domain.todos.entity import Todo
from todos_app.infrastructure.persistence.todos import mapper
from todos_app.infrastructure.persistence.todos.orm import TodoModel


pytestmark = pytest.mark.unit


def test_to_entity_maps_nullable_fields() -> None:
	orm = TodoModel(
		id=TEST_TODO_ID,
		title="Task",
		description=None,
		priority=None,
		completed=False,
		owner_id=TEST_USER_ID,
	)
	entity = mapper.to_entity(orm)
	assert entity.title == "Task"
	assert entity.description is None
	assert entity.priority is None


def test_to_orm_round_trip_preserves_fields() -> None:
	entity = Todo(
		id=TEST_TODO_ID,
		title="Task",
		description="Details",
		priority="high",
		completed=True,
		owner_id=TEST_USER_ID,
	)
	orm = mapper.to_orm(entity, id=TEST_TODO_ID)
	round_tripped = mapper.to_entity(orm)
	assert round_tripped == entity


def test_to_orm_round_trip_with_null_optional_fields() -> None:
	entity = Todo(
		id=TEST_TODO_ID,
		title="Minimal",
		description=None,
		priority=None,
		completed=False,
		owner_id=TEST_USER_ID,
	)
	round_tripped = mapper.to_entity(mapper.to_orm(entity, id=TEST_TODO_ID))
	assert round_tripped == entity
