from dataclasses import dataclass
from uuid import UUID


@dataclass
class Todo:
	id: UUID | None
	title: str
	description: str | None
	priority: str | None
	completed: bool
	owner_id: UUID
