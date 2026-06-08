from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from todos_app.core.http_errors import DATABASE_CONSTRAINT_VIOLATION, DATABASE_ERROR


DATABASE_INTEGRITY_ERROR_TYPE = "database_integrity_error"
DATABASE_ERROR_TYPE = "database_error"


class ValidationErrorDetail(BaseModel):
	loc: list[str | int]
	msg: str
	type: str
	ctx: dict[str, str] | None = None


def _database_error_cause(exc: SQLAlchemyError) -> str:
	if isinstance(exc, IntegrityError) and exc.orig is not None:
		return str(exc.orig)
	return str(exc)


def is_duplicate_user_violation(exc: IntegrityError) -> bool:
	if exc.orig is None:
		return False
	message = str(exc.orig).lower()
	return (
		"users.email" in message
		or "users.username" in message
		or ("unique" in message and ("email" in message or "username" in message))
	)


def database_validation_error_detail(
	*,
	msg: str,
	error_type: str,
	cause: str | None = None,
	include_cause: bool = True,
) -> list[dict[str, object]]:
	ctx = {"cause": cause} if include_cause and cause is not None else None
	return [
		ValidationErrorDetail(
			loc=["database"],
			msg=msg,
			type=error_type,
			ctx=ctx,
		).model_dump(exclude_none=True)
	]


def database_http_exception(
	*,
	status_code: int,
	msg: str,
	error_type: str,
	exc: SQLAlchemyError,
	include_cause: bool = True,
) -> HTTPException:
	cause = _database_error_cause(exc) if include_cause else None
	return HTTPException(
		status_code=status_code,
		detail=database_validation_error_detail(
			msg=msg,
			error_type=error_type,
			cause=cause,
			include_cause=include_cause,
		),
	)


def database_error_openapi_example(
	msg: str,
	error_type: str,
	*,
	cause: str = "UNIQUE constraint failed: users.email",
) -> list[dict[str, object]]:
	return database_validation_error_detail(msg=msg, error_type=error_type, cause=cause)


DATABASE_READ_OPENAPI_EXAMPLE = database_error_openapi_example(
	DATABASE_ERROR,
	DATABASE_ERROR_TYPE,
	cause="no such table: todos",
)
DATABASE_CONFLICT_OPENAPI_EXAMPLE = database_error_openapi_example(
	DATABASE_CONSTRAINT_VIOLATION,
	DATABASE_INTEGRITY_ERROR_TYPE,
)
