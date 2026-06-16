"""Integration tests for security fixes (H1, M3, L5)."""

import pytest
from httpx import AsyncClient

from integration.api.helpers import auth_headers, register_admin_and_login, register_and_login


pytestmark = pytest.mark.integration


async def test_given_password_changed_when_using_old_token_then_returns_401(client: AsyncClient) -> None:
	"""H1: After changing password, the old JWT must be rejected (401)."""
	# given
	user = await register_and_login(client)
	await client.patch(
		"/users/me",
		json={
			"password": "newpassword123",
			"current_password": user.payload["password"],
		},
		headers=auth_headers(user.token),
	)

	# when
	me_response = await client.get("/users/me", headers=auth_headers(user.token))

	# then
	assert me_response.status_code == 401


async def test_given_password_changed_when_logging_in_with_new_password_then_accepts_new_token(
	client: AsyncClient,
) -> None:
	"""H1: A freshly issued token after password change must be accepted."""
	# given
	user = await register_and_login(client)
	await client.patch(
		"/users/me",
		json={
			"password": "newpassword123",
			"current_password": user.payload["password"],
		},
		headers=auth_headers(user.token),
	)

	# when
	login_response = await client.post(
		"/auth/login",
		json={"username": user.payload["username"], "password": "newpassword123"},
	)
	new_token = login_response.json()["access_token"]
	me_response = await client.get("/users/me", headers=auth_headers(new_token))

	# then
	assert login_response.status_code == 200
	assert me_response.status_code == 200


async def test_given_authenticated_user_when_changing_password_without_current_password_then_returns_403(
	client: AsyncClient,
) -> None:
	"""M3: Changing password without current_password returns 403."""
	# given
	user = await register_and_login(client)

	# when
	response = await client.patch(
		"/users/me",
		json={"password": "newpassword123"},
		headers=auth_headers(user.token),
	)

	# then
	assert response.status_code == 403
	assert "current password" in response.json()["detail"].lower()


async def test_given_authenticated_user_when_changing_password_with_wrong_current_password_then_returns_403(
	client: AsyncClient,
) -> None:
	"""M3: Wrong current_password returns 403."""
	# given
	user = await register_and_login(client)

	# when
	response = await client.patch(
		"/users/me",
		json={"password": "newpassword123", "current_password": "wrongpassword"},
		headers=auth_headers(user.token),
	)

	# then
	assert response.status_code == 403


async def test_given_authenticated_user_when_changing_password_with_correct_current_password_then_returns_200(
	client: AsyncClient,
) -> None:
	"""M3: Correct current_password allows password change."""
	# given
	user = await register_and_login(client)

	# when
	response = await client.patch(
		"/users/me",
		json={"password": "newpassword123", "current_password": user.payload["password"]},
		headers=auth_headers(user.token),
	)

	# then
	assert response.status_code == 200


async def test_given_last_active_admin_when_soft_deleting_self_then_returns_409(client: AsyncClient) -> None:
	"""L5: Soft-deleting the last active admin returns 409."""
	# given
	admin = await register_admin_and_login(client)

	# when
	response = await client.delete(f"/users/{admin.user_id}", headers=auth_headers(admin.token))

	# then
	assert response.status_code == 409


async def test_given_last_active_admin_when_hard_deleting_self_then_returns_409(client: AsyncClient) -> None:
	"""L5: Hard-deleting the last active admin returns 409."""
	# given
	admin = await register_admin_and_login(client)

	# when
	response = await client.delete(
		f"/users/{admin.user_id}",
		params={"hard": "true"},
		headers=auth_headers(admin.token),
	)

	# then
	assert response.status_code == 409


async def test_given_two_active_admins_when_deleting_one_then_returns_204(client: AsyncClient) -> None:
	"""L5: Deleting an admin succeeds when at least one other active admin exists."""
	# given
	admin_1 = await register_admin_and_login(client)
	admin_2 = await register_admin_and_login(client)

	# when
	response = await client.delete(f"/users/{admin_1.user_id}", headers=auth_headers(admin_2.token))

	# then
	assert response.status_code == 204
