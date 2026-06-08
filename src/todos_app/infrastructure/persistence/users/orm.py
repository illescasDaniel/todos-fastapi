from uuid import UUID

from sqlalchemy import String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from todos_app.domain.users.field_limits import (
	EMAIL_MAX_LENGTH,
	FIRST_NAME_MAX_LENGTH,
	HASHED_PASSWORD_MAX_LENGTH,
	LAST_NAME_MAX_LENGTH,
	ROLE_MAX_LENGTH,
	USERNAME_MAX_LENGTH,
)
from todos_app.infrastructure.persistence.database import Base


class UserModel(Base):
	__tablename__ = "users"
	id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
	email: Mapped[str] = mapped_column(String(EMAIL_MAX_LENGTH), unique=True)
	username: Mapped[str] = mapped_column(String(USERNAME_MAX_LENGTH), unique=True)
	first_name: Mapped[str] = mapped_column(String(FIRST_NAME_MAX_LENGTH))
	last_name: Mapped[str] = mapped_column(String(LAST_NAME_MAX_LENGTH))
	hashed_password: Mapped[str] = mapped_column(String(HASHED_PASSWORD_MAX_LENGTH))
	is_active: Mapped[bool] = mapped_column(default=True)
	role: Mapped[str] = mapped_column(String(ROLE_MAX_LENGTH))
