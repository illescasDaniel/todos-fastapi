from todos_app.users.domain.entity import User
from todos_app.users.domain.repository import UserRepository


async def create_user(entity: User, *, repo: UserRepository) -> User:
	normalized = User(
		id=entity.id,
		email=entity.email,
		username=entity.username.lower(),
		first_name=entity.first_name,
		last_name=entity.last_name,
		hashed_password=entity.hashed_password,
		is_active=entity.is_active,
		role=entity.role,
		token_version=entity.token_version,
	)
	return await repo.add(normalized)
