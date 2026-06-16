from collections.abc import Iterable
from uuid import UUID

from todos_app.domain.todos.entity import Todo
from todos_app.infrastructure.persistence.todos.orm import TodoModel


def to_entity(orm: TodoModel) -> Todo:
	return Todo(
		id=orm.id,
		title=orm.title,
		description=orm.description,
		priority=orm.priority,
		completed=orm.completed,
		owner_id=orm.owner_id,
	)


def to_entities(orms: Iterable[TodoModel]) -> list[Todo]:
	return [to_entity(orm) for orm in orms]


def require_owner_id(entity: Todo) -> UUID:
	if entity.owner_id is None:
		raise ValueError("todo owner_id must be set before persist")
	return entity.owner_id


def to_orm(entity: Todo, *, id: UUID) -> TodoModel:
	return TodoModel(
		id=id,
		title=entity.title,
		description=entity.description,
		priority=entity.priority,
		completed=entity.completed,
		owner_id=require_owner_id(entity),
	)
