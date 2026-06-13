from mcp.server.fastmcp import FastMCP

from todos_mcp.client import ApiClient
from todos_mcp.config import Settings
from todos_mcp.tools._helpers import missing_token_response, resolve_access_token


def register(mcp: FastMCP, settings: Settings, client: ApiClient) -> None:
	@mcp.tool()
	async def todos_list(
		limit: int = 20,
		last_id: str | None = None,
		access_token: str | None = None,
	) -> str:
		"""List todos with cursor pagination (GET /todos). Limit 1-100."""
		token = resolve_access_token(access_token)
		if not token:
			return missing_token_response()
		params: dict[str, str | int] = {"limit": limit}
		if last_id is not None:
			params["last_id"] = last_id
		return await client.request("GET", "/todos", params=params, access_token=token)

	@mcp.tool()
	async def todos_get(todo_id: str, access_token: str | None = None) -> str:
		"""Get one todo by id (GET /todos/{todo_id})."""
		token = resolve_access_token(access_token)
		if not token:
			return missing_token_response()
		return await client.request("GET", f"/todos/{todo_id}", access_token=token)

	@mcp.tool()
	async def todos_create(
		title: str,
		description: str | None = None,
		priority: str | None = None,
		completed: bool = False,
		owner_id: str | None = None,
		access_token: str | None = None,
	) -> str:
		"""Create a todo (POST /todos). Title 1-200 chars. Admins may set owner_id."""
		token = resolve_access_token(access_token)
		if not token:
			return missing_token_response()
		body: dict[str, str | bool] = {"title": title, "completed": completed}
		if description is not None:
			body["description"] = description
		if priority is not None:
			body["priority"] = priority
		if owner_id is not None:
			body["owner_id"] = owner_id
		return await client.request("POST", "/todos", json_body=body, access_token=token)

	@mcp.tool()
	async def todos_replace(
		todo_id: str,
		title: str,
		description: str | None = None,
		priority: str | None = None,
		completed: bool = False,
		owner_id: str | None = None,
		access_token: str | None = None,
	) -> str:
		"""Full replace of a todo (PUT /todos/{todo_id})."""
		token = resolve_access_token(access_token)
		if not token:
			return missing_token_response()
		body: dict[str, str | bool] = {"title": title, "completed": completed}
		if description is not None:
			body["description"] = description
		if priority is not None:
			body["priority"] = priority
		if owner_id is not None:
			body["owner_id"] = owner_id
		return await client.request(
			"PUT",
			f"/todos/{todo_id}",
			json_body=body,
			access_token=token,
		)

	@mcp.tool()
	async def todos_patch(
		todo_id: str,
		title: str | None = None,
		description: str | None = None,
		priority: str | None = None,
		completed: bool | None = None,
		owner_id: str | None = None,
		access_token: str | None = None,
	) -> str:
		"""Partial update of a todo (PATCH /todos/{todo_id})."""
		token = resolve_access_token(access_token)
		if not token:
			return missing_token_response()
		body: dict[str, str | bool] = {}
		for key, value in (
			("title", title),
			("description", description),
			("priority", priority),
			("completed", completed),
			("owner_id", owner_id),
		):
			if value is not None:
				body[key] = value
		return await client.request(
			"PATCH",
			f"/todos/{todo_id}",
			json_body=body,
			access_token=token,
		)

	@mcp.tool()
	async def todos_delete(todo_id: str, access_token: str | None = None) -> str:
		"""Delete a todo (DELETE /todos/{todo_id}). Returns 204 on success."""
		token = resolve_access_token(access_token)
		if not token:
			return missing_token_response()
		return await client.request("DELETE", f"/todos/{todo_id}", access_token=token)
