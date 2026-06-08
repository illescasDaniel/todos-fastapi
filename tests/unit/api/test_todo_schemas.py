import pytest
from pydantic import ValidationError

from todos_app.api.todos.schemas import TodoCreate, TodoPatch, TodoUpdate


pytestmark = pytest.mark.unit


def test_create_accepts_null_description_and_priority() -> None:
	body = TodoCreate(title="Task only")
	assert body.description is None
	assert body.priority is None


def test_create_rejects_empty_title() -> None:
	with pytest.raises(ValidationError):
		TodoCreate(title="", description=None, priority=None)


def test_create_rejects_empty_description() -> None:
	with pytest.raises(ValidationError):
		TodoCreate(title="Task", description="", priority=None)


def test_update_rejects_empty_priority() -> None:
	with pytest.raises(ValidationError):
		TodoUpdate(title="Task", description=None, priority="")


def test_patch_rejects_null_title() -> None:
	with pytest.raises(ValidationError):
		TodoPatch(title=None)


def test_patch_rejects_empty_description() -> None:
	with pytest.raises(ValidationError):
		TodoPatch(description="")


def test_patch_accepts_null_description() -> None:
	body = TodoPatch(description=None)
	assert body.description is None
