"""Integration tests for security fixes (H1, M3, L5)."""

import pytest
from httpx import AsyncClient

from integration.api.helpers import auth_headers, register_admin_and_login, register_and_login


pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# H1 — JWT revoked on password change
# ---------------------------------------------------------------------------


async def test_old_token_rejected_after_password_change(client: AsyncClient) -> None:
	"""H1: After changing password, the old JWT must be rejected (401)."""
	payload, old_token = await register_and_login(client)

	patch_response = await client.patch(
		"/users/me",
		json={
			"password": "newpassword123",
			"current_password": payload["password"],
		},
		headers=auth_headers(old_token),
	)
	assert patch_response.status_code == 200

	me_response = await client.get("/users/me", headers=auth_headers(old_token))
	assert me_response.status_code == 401


async def test_new_token_works_after_password_change(client: AsyncClient) -> None:
	"""H1: A freshly issued token after password change must be accepted."""
	payload, old_token = await register_and_login(client)

	await client.patch(
		"/users/me",
		json={
			"password": "newpassword123",
			"current_password": payload["password"],
		},
		headers=auth_headers(old_token),
	)

	login_response = await client.post(
		"/auth/login",
		json={"username": payload["username"], "password": "newpassword123"},
	)
	assert login_response.status_code == 200
	new_token = login_response.json()["access_token"]

	me_response = await client.get("/users/me", headers=auth_headers(new_token))
	assert me_response.status_code == 200


# ---------------------------------------------------------------------------
# M3 — Step-up auth for password change
# ---------------------------------------------------------------------------


async def test_password_change_requires_current_password(client: AsyncClient) -> None:
	"""M3: Changing password without current_password returns 403."""
	_, token = await register_and_login(client)

	response = await client.patch(
		"/users/me",
		json={"password": "newpassword123"},
		headers=auth_headers(token),
	)
	assert response.status_code == 403
	assert "current password" in response.json()["detail"].lower()


async def test_password_change_with_wrong_current_password_returns_403(client: AsyncClient) -> None:
	"""M3: Wrong current_password returns 403."""
	_, token = await register_and_login(client)

	response = await client.patch(
		"/users/me",
		json={"password": "newpassword123", "current_password": "wrongpassword"},
		headers=auth_headers(token),
	)
	assert response.status_code == 403


async def test_password_change_succeeds_with_correct_current_password(client: AsyncClient) -> None:
	"""M3: Correct current_password allows password change."""
	payload, token = await register_and_login(client)

	response = await client.patch(
		"/users/me",
		json={"password": "newpassword123", "current_password": payload["password"]},
		headers=auth_headers(token),
	)
	assert response.status_code == 200


# ---------------------------------------------------------------------------
# L5 — Last admin guard
# ---------------------------------------------------------------------------


async def test_cannot_deactivate_last_admin(client: AsyncClient) -> None:
	"""L5: Soft-deleting the last active admin returns 409."""
	_, admin_token = await register_admin_and_login(client)
	admin_id = (await client.get("/users/me", headers=auth_headers(admin_token))).json()["id"]

	response = await client.delete(f"/users/{admin_id}", headers=auth_headers(admin_token))
	assert response.status_code == 409


async def test_cannot_hard_delete_last_admin(client: AsyncClient) -> None:
	"""L5: Hard-deleting the last active admin returns 409."""
	_, admin_token = await register_admin_and_login(client)
	admin_id = (await client.get("/users/me", headers=auth_headers(admin_token))).json()["id"]

	response = await client.delete(
		f"/users/{admin_id}",
		params={"hard": "true"},
		headers=auth_headers(admin_token),
	)
	assert response.status_code == 409


async def test_can_delete_admin_when_another_exists(client: AsyncClient) -> None:
	"""L5: Deleting an admin succeeds when at least one other active admin exists."""
	_, admin_token_1 = await register_admin_and_login(client)
	_, admin_token_2 = await register_admin_and_login(client)
	admin_id_1 = (await client.get("/users/me", headers=auth_headers(admin_token_1))).json()["id"]

	response = await client.delete(f"/users/{admin_id_1}", headers=auth_headers(admin_token_2))
	assert response.status_code == 204
