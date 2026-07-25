from todos_app.auth.domain.user_lookup import UserCredentials
from todos_app.users.domain.repository import UserRepository


class UserRepositoryLookup:
	"""Adapts UserRepository to the auth UserLookup port."""

	def __init__(self, repo: UserRepository) -> None:
		self._repo = repo

	async def get_by_username(self, username: str) -> UserCredentials | None:
		user = await self._repo.get_by_username(username)
		if user is None or user.id is None:
			return None
		return UserCredentials(
			id=user.id,
			username=user.username,
			hashed_password=user.hashed_password,
			is_active=user.is_active,
			role=user.role,
			token_version=user.token_version,
		)
