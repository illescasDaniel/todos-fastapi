from dataclasses import dataclass
from uuid import UUID

from todos_app.domain.todos.entity import Todo


@dataclass(frozen=True)
class TodoPage:
	items: list[Todo]
	next_last_id: UUID | None
