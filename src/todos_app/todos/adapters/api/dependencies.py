from typing import Annotated

from fastapi import Depends

from todos_app.shared.dependencies import DbSessionDep
from todos_app.todos.adapters.database.repository import SqlAlchemyTodoRepository
from todos_app.todos.domain.repository import TodoRepository


def get_todo_repository(db: DbSessionDep) -> TodoRepository:
	return SqlAlchemyTodoRepository(db)


TodoRepositoryDep = Annotated[TodoRepository, Depends(get_todo_repository)]
