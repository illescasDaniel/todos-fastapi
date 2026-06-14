from uuid import UUID

from fastapi import APIRouter, Query, Request, status

from todos_app.api.openapi_responses import OpenAPIResponse
from todos_app.api.users import mappers
from todos_app.api.users.schemas import (
	UserAdminPatch,
	UserAdminReplace,
	UserResponse,
	UserSelfPatch,
	UserSelfReplace,
	UserSignup,
)
from todos_app.application import users as user_use_cases
from todos_app.core.auth import CurrentUserDep
from todos_app.core.dependencies import PasswordHasherDep, UserAuthCacheDep, UserRepositoryDep
from todos_app.core.rate_limiting import limiter
from todos_app.domain.auth.authorization import require_admin


router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
	"",
	response_model=UserResponse,
	status_code=status.HTTP_201_CREATED,
	responses=OpenAPIResponse.merge_write(),
)
@limiter.limit("10/minute")  # pyright: ignore[reportUntypedFunctionDecorator,reportUnknownMemberType]
async def create_user(
	request: Request, user: UserSignup, repo: UserRepositoryDep, hasher: PasswordHasherDep
) -> UserResponse:
	created_user = await user_use_cases.create_user(
		mappers.signup_to_entity(user, hasher),
		repo=repo,
	)
	return mappers.to_response(created_user)


@router.get(
	"/me",
	response_model=UserResponse,
	responses=OpenAPIResponse.merge_authenticated_read(OpenAPIResponse.USER_NOT_FOUND),
)
async def get_me(repo: UserRepositoryDep, current_user: CurrentUserDep) -> UserResponse:
	user = await user_use_cases.get_user_by_id(repo, current_user.user_id)
	return mappers.to_response(user)


@router.put(
	"/me",
	response_model=UserResponse,
	responses=OpenAPIResponse.merge_authenticated_write(OpenAPIResponse.USER_NOT_FOUND),
)
async def replace_me(
	body: UserSelfReplace,
	repo: UserRepositoryDep,
	hasher: PasswordHasherDep,
	current_user: CurrentUserDep,
	auth_cache: UserAuthCacheDep,
) -> UserResponse:
	user = await user_use_cases.update_user(
		current_user.user_id,
		lambda existing: mappers.apply_user_self_replace(existing, body, hasher),
		repo=repo,
		auth_cache=auth_cache,
	)
	return mappers.to_response(user)


@router.patch(
	"/me",
	response_model=UserResponse,
	responses=OpenAPIResponse.merge_authenticated_write(OpenAPIResponse.USER_NOT_FOUND),
)
async def patch_me(
	body: UserSelfPatch,
	repo: UserRepositoryDep,
	hasher: PasswordHasherDep,
	current_user: CurrentUserDep,
	auth_cache: UserAuthCacheDep,
) -> UserResponse:
	fields = mappers.self_patch_fields(body)
	user = await user_use_cases.update_user(
		current_user.user_id,
		lambda existing: mappers.apply_user_patch(existing, fields, hasher),
		repo=repo,
		auth_cache=auth_cache,
	)
	return mappers.to_response(user)


@router.put(
	"/{user_id}",
	response_model=UserResponse,
	responses=OpenAPIResponse.merge_authenticated_write(OpenAPIResponse.USER_NOT_FOUND),
)
async def replace_user(
	user_id: UUID,
	body: UserAdminReplace,
	repo: UserRepositoryDep,
	hasher: PasswordHasherDep,
	current_user: CurrentUserDep,
	auth_cache: UserAuthCacheDep,
) -> UserResponse:
	require_admin(current_user.role)
	user = await user_use_cases.update_user(
		user_id,
		lambda existing: mappers.apply_user_admin_replace(existing, body, hasher),
		repo=repo,
		auth_cache=auth_cache,
	)
	return mappers.to_response(user)


@router.patch(
	"/{user_id}",
	response_model=UserResponse,
	responses=OpenAPIResponse.merge_authenticated_write(OpenAPIResponse.USER_NOT_FOUND),
)
async def patch_user(
	user_id: UUID,
	body: UserAdminPatch,
	repo: UserRepositoryDep,
	hasher: PasswordHasherDep,
	current_user: CurrentUserDep,
	auth_cache: UserAuthCacheDep,
) -> UserResponse:
	require_admin(current_user.role)
	fields = mappers.admin_patch_fields(body)
	user = await user_use_cases.update_user(
		user_id,
		lambda existing: mappers.apply_user_patch(existing, fields, hasher),
		repo=repo,
		auth_cache=auth_cache,
	)
	return mappers.to_response(user)


@router.delete(
	"/{user_id}",
	status_code=status.HTTP_204_NO_CONTENT,
	responses=OpenAPIResponse.merge_authenticated_write(OpenAPIResponse.USER_NOT_FOUND),
)
async def delete_user(
	user_id: UUID,
	repo: UserRepositoryDep,
	current_user: CurrentUserDep,
	auth_cache: UserAuthCacheDep,
	hard: bool = Query(
		default=False,
		description="When true, permanently delete the user and all of their todos.",
	),
) -> None:
	require_admin(current_user.role)
	if hard:
		await user_use_cases.hard_delete_user(user_id, repo=repo, auth_cache=auth_cache)
	else:
		await user_use_cases.deactivate_user(user_id, repo=repo, auth_cache=auth_cache)
