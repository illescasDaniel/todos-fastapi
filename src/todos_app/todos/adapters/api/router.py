from uuid import UUID

from fastapi import APIRouter, Query, status

from todos_app.auth.adapters.api.current_user import CurrentUserDep
from todos_app.shared.adapters.api.openapi_responses import OpenAPIResponse
from todos_app.shared.settings import get_settings
from todos_app.todos.adapters.api import mappers
from todos_app.todos.adapters.api.dependencies import TodoRepositoryDep
from todos_app.todos.adapters.api.schemas import TodoCreate, TodoListResponse, TodoPatch, TodoResponse, TodoUpdate
from todos_app.todos.application.create_todo import create_todo_for_actor
from todos_app.todos.application.delete_todo import delete_todo_for_actor
from todos_app.todos.application.get_todo import get_todo_for_actor
from todos_app.todos.application.list_todos import list_todos_for_actor
from todos_app.todos.application.update_todo import update_todo_for_actor


settings = get_settings()

router = APIRouter(prefix="/todos", tags=["ToDos"])


@router.get(
	"",
	response_model=TodoListResponse,
	responses=OpenAPIResponse.merge_authenticated_read(),
)
async def list_todos(
	repo: TodoRepositoryDep,
	current_user: CurrentUserDep,
	last_id: UUID | None = Query(
		None,
		description="Return todos with ids greater than this value. Omit for the first page.",
	),
	limit: int = Query(
		settings.api.pagination_default_limit,
		ge=1,
		le=settings.api.pagination_max_limit,
		description="Maximum number of todos to return.",
	),
) -> TodoListResponse:
	page = await list_todos_for_actor(
		repo,
		last_id=last_id,
		limit=limit,
		actor_id=current_user.user_id,
		actor_role=current_user.role,
	)
	return TodoListResponse(
		items=mappers.to_response_list(page.items),
		next_last_id=page.next_last_id,
		limit=limit,
	)


@router.get(
	"/{todo_id}",
	response_model=TodoResponse,
	responses=OpenAPIResponse.merge_authenticated_read(OpenAPIResponse.TODO_NOT_IN_ACTOR_SCOPE),
)
async def get_todo(
	todo_id: UUID,
	repo: TodoRepositoryDep,
	current_user: CurrentUserDep,
) -> TodoResponse:
	todo = await get_todo_for_actor(
		repo,
		todo_id,
		actor_id=current_user.user_id,
		actor_role=current_user.role,
	)
	return mappers.to_response(todo)


@router.post(
	"",
	response_model=TodoResponse,
	status_code=status.HTTP_201_CREATED,
	responses=OpenAPIResponse.merge_authenticated_write(),
)
async def create_todo(
	todo: TodoCreate,
	repo: TodoRepositoryDep,
	current_user: CurrentUserDep,
) -> TodoResponse:
	created_todo = await create_todo_for_actor(
		repo,
		mappers.create_to_entity(todo),
		actor_id=current_user.user_id,
		actor_role=current_user.role,
		requested_owner_id=todo.owner_id,
	)
	return mappers.to_response(created_todo)


@router.put(
	"/{todo_id}",
	response_model=TodoResponse,
	responses=OpenAPIResponse.merge_authenticated_write(
		OpenAPIResponse.TODO_NOT_IN_ACTOR_SCOPE,
		OpenAPIResponse.TODO_OWNER_CHANGE_FORBIDDEN,
	),
)
async def update_todo(
	todo_id: UUID,
	todo: TodoUpdate,
	repo: TodoRepositoryDep,
	current_user: CurrentUserDep,
) -> TodoResponse:
	updated_todo = await update_todo_for_actor(
		repo,
		todo_id,
		lambda _existing, owner_id: mappers.update_to_entity(todo, todo_id, owner_id),
		actor_id=current_user.user_id,
		actor_role=current_user.role,
		requested_owner_id=todo.owner_id,
	)
	return mappers.to_response(updated_todo)


@router.patch(
	"/{todo_id}",
	response_model=TodoResponse,
	responses=OpenAPIResponse.merge_authenticated_write(
		OpenAPIResponse.TODO_NOT_IN_ACTOR_SCOPE,
		OpenAPIResponse.TODO_OWNER_CHANGE_FORBIDDEN,
	),
)
async def patch_todo(
	todo_id: UUID,
	todo: TodoPatch,
	repo: TodoRepositoryDep,
	current_user: CurrentUserDep,
) -> TodoResponse:
	fields = mappers.patch_fields(todo)
	updated_todo = await update_todo_for_actor(
		repo,
		todo_id,
		lambda existing, owner_id: mappers.apply_todo_patch(existing, fields, owner_id),
		actor_id=current_user.user_id,
		actor_role=current_user.role,
		requested_owner_id=fields.get("owner_id"),
	)
	return mappers.to_response(updated_todo)


@router.delete(
	"/{todo_id}",
	status_code=status.HTTP_204_NO_CONTENT,
	responses=OpenAPIResponse.merge_authenticated_write(OpenAPIResponse.TODO_NOT_IN_ACTOR_SCOPE),
)
async def delete_todo(todo_id: UUID, repo: TodoRepositoryDep, current_user: CurrentUserDep) -> None:
	await delete_todo_for_actor(
		repo,
		todo_id,
		actor_id=current_user.user_id,
		actor_role=current_user.role,
	)
