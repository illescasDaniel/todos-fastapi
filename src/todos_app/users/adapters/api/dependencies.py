from typing import Annotated

from fastapi import Depends

from todos_app.shared.dependencies import DbSessionDep
from todos_app.users.adapters.database.repository import SqlAlchemyUserRepository
from todos_app.users.domain.repository import UserRepository


def get_user_repository(db: DbSessionDep) -> UserRepository:
	return SqlAlchemyUserRepository(db)


UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]
