from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exception_handlers import http_exception_handler
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.responses import Response

from todos_app.application.errors import (
	CurrentPasswordInvalidError,
	CurrentPasswordRequiredError,
	InvalidCredentialsError,
	LastAdminError,
	TodoNotFoundError,
	TodoOwnerChangeForbiddenError,
	UserNotFoundError,
)
from todos_app.core.error_responses import (
	DATABASE_ERROR_TYPE,
	DATABASE_INTEGRITY_ERROR_TYPE,
	database_http_exception,
	is_duplicate_user_violation,
)
from todos_app.core.http_errors import (
	CURRENT_PASSWORD_INVALID,
	CURRENT_PASSWORD_REQUIRED,
	DATABASE_CONSTRAINT_VIOLATION,
	DATABASE_ERROR,
	DUPLICATE_USER,
	FORBIDDEN,
	INVALID_CREDENTIALS,
	LAST_ADMIN,
	TODO_NOT_FOUND,
	TODO_NOT_FOUND_FOR_ACTOR,
	TODO_OWNER_CHANGE_FORBIDDEN,
	USER_NOT_FOUND,
)
from todos_app.core.logging import logger
from todos_app.core.settings import get_settings
from todos_app.domain.auth.authorization import ADMIN_ROLE, AdminRequiredError


async def integrity_error_handler(request: Request, exc: Exception) -> Response:
	assert isinstance(exc, IntegrityError)
	logger.exception("Database integrity error", exc_info=exc)
	settings = get_settings()
	include_cause = settings.exposes_error_details()
	if is_duplicate_user_violation(exc):
		# M2: return 400 with generic message to avoid account enumeration
		http_exc = database_http_exception(
			status_code=status.HTTP_400_BAD_REQUEST,
			msg=DUPLICATE_USER,
			error_type=DATABASE_INTEGRITY_ERROR_TYPE,
			exc=exc,
			include_cause=False,
		)
	else:
		http_exc = database_http_exception(
			status_code=status.HTTP_409_CONFLICT,
			msg=DATABASE_CONSTRAINT_VIOLATION,
			error_type=DATABASE_INTEGRITY_ERROR_TYPE,
			exc=exc,
			include_cause=include_cause,
		)
	return await http_exception_handler(request, http_exc)


async def sqlalchemy_error_handler(request: Request, exc: Exception) -> Response:
	assert isinstance(exc, SQLAlchemyError)
	logger.exception("Database error", exc_info=exc)
	settings = get_settings()
	http_exc = database_http_exception(
		status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
		msg=DATABASE_ERROR,
		error_type=DATABASE_ERROR_TYPE,
		exc=exc,
		include_cause=settings.exposes_error_details(),
	)
	return await http_exception_handler(request, http_exc)


async def invalid_credentials_handler(request: Request, exc: Exception) -> Response:
	assert isinstance(exc, InvalidCredentialsError)
	http_exc = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_CREDENTIALS)
	return await http_exception_handler(request, http_exc)


async def user_not_found_handler(request: Request, exc: Exception) -> Response:
	assert isinstance(exc, UserNotFoundError)
	http_exc = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=USER_NOT_FOUND)
	return await http_exception_handler(request, http_exc)


async def todo_not_found_handler(request: Request, exc: Exception) -> Response:
	assert isinstance(exc, TodoNotFoundError)
	detail = TODO_NOT_FOUND if exc.actor_role == ADMIN_ROLE else TODO_NOT_FOUND_FOR_ACTOR
	http_exc = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
	return await http_exception_handler(request, http_exc)


async def admin_required_handler(request: Request, exc: Exception) -> Response:
	assert isinstance(exc, AdminRequiredError)
	http_exc = HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=FORBIDDEN)
	return await http_exception_handler(request, http_exc)


async def todo_owner_change_forbidden_handler(request: Request, exc: Exception) -> Response:
	assert isinstance(exc, TodoOwnerChangeForbiddenError)
	http_exc = HTTPException(
		status_code=status.HTTP_403_FORBIDDEN,
		detail=TODO_OWNER_CHANGE_FORBIDDEN,
	)
	return await http_exception_handler(request, http_exc)


async def current_password_required_handler(request: Request, exc: Exception) -> Response:
	assert isinstance(exc, CurrentPasswordRequiredError)
	http_exc = HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=CURRENT_PASSWORD_REQUIRED)
	return await http_exception_handler(request, http_exc)


async def current_password_invalid_handler(request: Request, exc: Exception) -> Response:
	assert isinstance(exc, CurrentPasswordInvalidError)
	http_exc = HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=CURRENT_PASSWORD_INVALID)
	return await http_exception_handler(request, http_exc)


async def last_admin_handler(request: Request, exc: Exception) -> Response:
	assert isinstance(exc, LastAdminError)
	http_exc = HTTPException(status_code=status.HTTP_409_CONFLICT, detail=LAST_ADMIN)
	return await http_exception_handler(request, http_exc)


def register_exception_handlers(app: FastAPI) -> None:
	app.add_exception_handler(IntegrityError, integrity_error_handler)
	app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)
	app.add_exception_handler(InvalidCredentialsError, invalid_credentials_handler)
	app.add_exception_handler(UserNotFoundError, user_not_found_handler)
	app.add_exception_handler(TodoNotFoundError, todo_not_found_handler)
	app.add_exception_handler(AdminRequiredError, admin_required_handler)
	app.add_exception_handler(TodoOwnerChangeForbiddenError, todo_owner_change_forbidden_handler)
	app.add_exception_handler(CurrentPasswordRequiredError, current_password_required_handler)
	app.add_exception_handler(CurrentPasswordInvalidError, current_password_invalid_handler)
	app.add_exception_handler(LastAdminError, last_admin_handler)
