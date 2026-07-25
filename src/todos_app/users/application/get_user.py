from uuid import UUID

from todos_app.users.application.errors import UserNotFoundError
from todos_app.users.domain.entity import User
from todos_app.users.domain.repository import UserRepository


async def get_user_by_id(repo: UserRepository, user_id: UUID) -> User:
	user = await repo.get_by_id(user_id)
	if user is None:
		raise UserNotFoundError
	return user
