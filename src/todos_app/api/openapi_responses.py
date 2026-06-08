from __future__ import annotations

from enum import Enum
from typing import Any

from fastapi import status

from todos_app.core.error_responses import (
	DATABASE_CONFLICT_OPENAPI_EXAMPLE,
	DATABASE_READ_OPENAPI_EXAMPLE,
)
from todos_app.core.http_errors import (
	FORBIDDEN,
	INVALID_CREDENTIALS,
	INVALID_TOKEN,
	TODO_NOT_FOUND,
	TODO_NOT_FOUND_FOR_ACTOR,
	TODO_OWNER_CHANGE_FORBIDDEN,
	USER_NOT_FOUND,
)


__all__ = ["OpenAPIResponse"]


class OpenAPIResponses(dict[int | str, dict[str, Any]]):
	pass


def _json_error_response(
	status_code: int,
	*,
	description: str,
	detail: str | list[dict[str, Any]] | dict[str, Any],
) -> OpenAPIResponses:
	return OpenAPIResponses(
		{
			status_code: {
				"description": description,
				"content": {"application/json": {"example": {"detail": detail}}},
			}
		}
	)


class OpenAPIResponse(Enum):
	TODO_NOT_FOUND = (
		status.HTTP_404_NOT_FOUND,
		"Todo not found",
		TODO_NOT_FOUND,
	)
	TODO_NOT_IN_ACTOR_SCOPE = (
		status.HTTP_404_NOT_FOUND,
		"Todo not in caller scope (missing or not owned; admins see global not found)",
		TODO_NOT_FOUND_FOR_ACTOR,
	)
	TODO_OWNER_CHANGE_FORBIDDEN = (
		status.HTTP_403_FORBIDDEN,
		"Non-admin cannot change todo owner",
		TODO_OWNER_CHANGE_FORBIDDEN,
	)
	USER_NOT_FOUND = (
		status.HTTP_404_NOT_FOUND,
		"User not found",
		USER_NOT_FOUND,
	)
	INVALID_CREDENTIALS = (
		status.HTTP_401_UNAUTHORIZED,
		"Invalid credentials",
		INVALID_CREDENTIALS,
	)
	INVALID_TOKEN = (
		status.HTTP_401_UNAUTHORIZED,
		"Missing or invalid bearer token",
		INVALID_TOKEN,
	)
	FORBIDDEN = (
		status.HTTP_403_FORBIDDEN,
		"Forbidden",
		FORBIDDEN,
	)
	DATABASE_READ = (
		status.HTTP_500_INTERNAL_SERVER_ERROR,
		"Database error",
		DATABASE_READ_OPENAPI_EXAMPLE,
	)
	DATABASE_CONFLICT = (
		status.HTTP_409_CONFLICT,
		(
			"Database constraint violation. Not expected with the current schema; "
			"documented for writes that may hit unique keys, foreign keys, or other "
			"constraints added later."
		),
		DATABASE_CONFLICT_OPENAPI_EXAMPLE,
	)

	status_code: int
	description: str
	detail: str | list[dict[str, Any]]

	def __init__(
		self,
		status_code: int,
		description: str,
		detail: str | list[dict[str, Any]],
	) -> None:
		self.status_code = status_code
		self.description = description
		self.detail = detail

	@property
	def openapi(self) -> OpenAPIResponses:
		return _json_error_response(
			self.status_code,
			description=self.description,
			detail=self.detail,
		)

	@classmethod
	def merge(cls, *members: OpenAPIResponse) -> OpenAPIResponses:
		merged = OpenAPIResponses()
		for member in members:
			merged.update(member.openapi)
		return merged

	@classmethod
	def merge_write(cls, *members: OpenAPIResponse) -> OpenAPIResponses:
		return cls.merge(cls.DATABASE_CONFLICT, cls.DATABASE_READ, *members)

	@classmethod
	def merge_authenticated_read(cls, *members: OpenAPIResponse) -> OpenAPIResponses:
		return cls.merge(cls.INVALID_TOKEN, cls.DATABASE_READ, *members)

	@classmethod
	def merge_authenticated_write(cls, *members: OpenAPIResponse) -> OpenAPIResponses:
		return cls.merge(cls.INVALID_TOKEN, cls.FORBIDDEN, cls.DATABASE_CONFLICT, cls.DATABASE_READ, *members)
