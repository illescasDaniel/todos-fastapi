import pytest
from pydantic import ValidationError

from todos_app.api.todos.schemas import TodoCreate, TodoPatch, TodoUpdate


pytestmark = pytest.mark.unit


def test_given_null_optional_fields_when_creating_todo_schema_then_accepts_body() -> None:
	# given
	title = "Task only"

	# when
	body = TodoCreate(title=title)

	# then
	assert body.description is None
	assert body.priority is None


def test_given_empty_title_when_creating_todo_schema_then_raises_validation_error() -> None:
	# given
	title = ""

	# when
	with pytest.raises(ValidationError):
		TodoCreate(title=title, description=None, priority=None)

	# then


def test_given_empty_description_when_creating_todo_schema_then_raises_validation_error() -> None:
	# given
	description = ""

	# when
	with pytest.raises(ValidationError):
		TodoCreate(title="Task", description=description, priority=None)

	# then


def test_given_empty_priority_when_updating_todo_schema_then_raises_validation_error() -> None:
	# given
	priority = ""

	# when
	with pytest.raises(ValidationError):
		TodoUpdate(title="Task", description=None, priority=priority)

	# then


def test_given_null_title_when_patching_todo_schema_then_raises_validation_error() -> None:
	# given

	# when
	with pytest.raises(ValidationError):
		TodoPatch(title=None)

	# then


def test_given_empty_description_when_patching_todo_schema_then_raises_validation_error() -> None:
	# given
	description = ""

	# when
	with pytest.raises(ValidationError):
		TodoPatch(description=description)

	# then


def test_given_null_description_when_patching_todo_schema_then_accepts_body() -> None:
	# given

	# when
	body = TodoPatch(description=None)

	# then
	assert body.description is None
