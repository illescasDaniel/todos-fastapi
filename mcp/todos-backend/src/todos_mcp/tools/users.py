from typing import Literal

from mcp.server.fastmcp import FastMCP

from todos_mcp.client import ApiClient
from todos_mcp.config import Settings
from todos_mcp.tools._helpers import missing_token_response, resolve_access_token


def register(mcp: FastMCP, settings: Settings, client: ApiClient) -> None:
    @mcp.tool()
    async def users_signup(
        email: str,
        username: str,
        first_name: str,
        last_name: str,
        password: str,
    ) -> str:
        """Public signup (POST /users). Always creates role=user. Password 8-128 chars."""
        return await client.request(
            "POST",
            "/users",
            json_body={
                "email": email,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "password": password,
            },
        )

    @mcp.tool()
    async def users_get_me(access_token: str | None = None) -> str:
        """Get the current user profile (GET /users/me). Requires Bearer token."""
        token = resolve_access_token(access_token)
        if not token:
            return missing_token_response()
        return await client.request("GET", "/users/me", access_token=token)

    @mcp.tool()
    async def users_replace_me(
        email: str,
        username: str,
        first_name: str,
        last_name: str,
        password: str | None = None,
        access_token: str | None = None,
    ) -> str:
        """Replace own profile (PUT /users/me). Omit password to keep current."""
        token = resolve_access_token(access_token)
        if not token:
            return missing_token_response()
        body: dict[str, str] = {
            "email": email,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
        }
        if password is not None:
            body["password"] = password
        return await client.request("PUT", "/users/me", json_body=body, access_token=token)

    @mcp.tool()
    async def users_patch_me(
        email: str | None = None,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        password: str | None = None,
        access_token: str | None = None,
    ) -> str:
        """Partially update own profile (PATCH /users/me)."""
        token = resolve_access_token(access_token)
        if not token:
            return missing_token_response()
        body: dict[str, str] = {}
        for key, value in (
            ("email", email),
            ("username", username),
            ("first_name", first_name),
            ("last_name", last_name),
            ("password", password),
        ):
            if value is not None:
                body[key] = value
        return await client.request("PATCH", "/users/me", json_body=body, access_token=token)

    @mcp.tool()
    async def users_admin_replace(
        user_id: str,
        email: str,
        username: str,
        first_name: str,
        last_name: str,
        role: Literal["user", "admin"],
        is_active: bool,
        password: str | None = None,
        access_token: str | None = None,
    ) -> str:
        """Replace any user (PUT /users/{user_id}). Admin only."""
        token = resolve_access_token(access_token)
        if not token:
            return missing_token_response()
        body: dict[str, str | bool] = {
            "email": email,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "role": role,
            "is_active": is_active,
        }
        if password is not None:
            body["password"] = password
        return await client.request(
            "PUT",
            f"/users/{user_id}",
            json_body=body,
            access_token=token,
        )

    @mcp.tool()
    async def users_admin_patch(
        user_id: str,
        email: str | None = None,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        password: str | None = None,
        role: Literal["user", "admin"] | None = None,
        is_active: bool | None = None,
        access_token: str | None = None,
    ) -> str:
        """Partially update any user (PATCH /users/{user_id}). Admin only."""
        token = resolve_access_token(access_token)
        if not token:
            return missing_token_response()
        body: dict[str, str | bool] = {}
        for key, value in (
            ("email", email),
            ("username", username),
            ("first_name", first_name),
            ("last_name", last_name),
            ("password", password),
            ("role", role),
            ("is_active", is_active),
        ):
            if value is not None:
                body[key] = value
        return await client.request(
            "PATCH",
            f"/users/{user_id}",
            json_body=body,
            access_token=token,
        )

    @mcp.tool()
    async def users_admin_delete(
        user_id: str,
        hard: bool = False,
        access_token: str | None = None,
    ) -> str:
        """Deactivate or permanently delete a user (DELETE /users/{user_id}). Admin only.

        Set hard=true to permanently delete the user and their todos.
        """
        token = resolve_access_token(access_token)
        if not token:
            return missing_token_response()
        return await client.request(
            "DELETE",
            f"/users/{user_id}",
            params={"hard": hard},
            access_token=token,
        )
