from uuid import UUID

from todos_app.users.adapters.database.orm import UserModel
from todos_app.users.domain.entity import User


def to_entity(orm: UserModel) -> User:
	return User(
		id=orm.id,
		email=orm.email,
		username=orm.username,
		first_name=orm.first_name,
		last_name=orm.last_name,
		hashed_password=orm.hashed_password,
		is_active=orm.is_active,
		role=orm.role,
		token_version=orm.token_version,
	)


def to_orm(entity: User, *, id: UUID) -> UserModel:
	return UserModel(
		id=id,
		email=entity.email,
		username=entity.username,
		first_name=entity.first_name,
		last_name=entity.last_name,
		hashed_password=entity.hashed_password,
		is_active=entity.is_active,
		role=entity.role,
		token_version=entity.token_version,
	)
