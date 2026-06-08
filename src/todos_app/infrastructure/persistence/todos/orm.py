from uuid import UUID

from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from todos_app.domain.todos.field_limits import (
	DESCRIPTION_MAX_LENGTH,
	PRIORITY_MAX_LENGTH,
	TITLE_MAX_LENGTH,
)
from todos_app.infrastructure.persistence.database import Base
from todos_app.infrastructure.persistence.users.orm import UserModel


class TodoModel(Base):
	__tablename__ = "todos"
	id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
	title: Mapped[str] = mapped_column(String(TITLE_MAX_LENGTH), nullable=False)
	description: Mapped[str | None] = mapped_column(String(DESCRIPTION_MAX_LENGTH), nullable=True)
	priority: Mapped[str | None] = mapped_column(String(PRIORITY_MAX_LENGTH), nullable=True)
	completed: Mapped[bool] = mapped_column(default=False)
	owner_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey(UserModel.id))
