import json

from mcp.server.fastmcp import FastMCP

from todos_mcp import session
from todos_mcp.client import ApiClient
from todos_mcp.config import Settings


def register(mcp: FastMCP, settings: Settings, client: ApiClient) -> None:
	@mcp.tool()
	async def auth_login(username: str, password: str) -> str:
		"""Authenticate with username and password (POST /auth/login).

		Username max 50 chars. Password 8-128 chars.
		Stores the access token in session for subsequent protected tools.
		"""
		response_text = await client.request(
			"POST",
			"/auth/login",
			json_body={"username": username, "password": password},
		)
		payload = json.loads(response_text)
		if payload.get("ok") and isinstance(payload.get("data"), dict):
			token = payload["data"].get("access_token")
			if isinstance(token, str):
				session.set_token(token)
		return response_text

	@mcp.tool()
	async def auth_clear_session() -> str:
		"""Clear the stored Bearer token from the MCP session."""
		session.clear_token()
		return json.dumps({"ok": True, "message": "Session cleared."}, indent=2)
