import pytest
from httpx import AsyncClient

from factories import user_signup_payload
from integration.api.helpers import auth_headers, register_admin_and_login, register_and_login


pytestmark = pytest.mark.integration


async def test_login_success(client: AsyncClient) -> None:
	payload = user_signup_payload()
	create_response = await client.post("/users", json=payload)
	assert create_response.status_code == 201

	login_response = await client.post(
		"/auth/login",
		json={"username": payload["username"], "password": payload["password"]},
	)
	assert login_response.status_code == 200
	body = login_response.json()
	assert body["access_token"]
	assert body["token_type"] == "bearer"


async def test_login_invalid_credentials(client: AsyncClient) -> None:
	response = await client.post(
		"/auth/login",
		json={"username": "nobody", "password": "wrongpass"},
	)
	assert response.status_code == 401


async def test_protected_route_without_token_returns_401(client: AsyncClient) -> None:
	response = await client.get("/todos")
	assert response.status_code == 401


async def test_deactivated_user_cannot_login(client: AsyncClient) -> None:
	target_payload, target_token = await register_and_login(client)
	_, admin_token = await register_admin_and_login(client)
	target_id = (await client.get("/users/me", headers=auth_headers(target_token))).json()["id"]

	deactivate_response = await client.delete(f"/users/{target_id}", headers=auth_headers(admin_token))
	assert deactivate_response.status_code == 204

	login_response = await client.post(
		"/auth/login",
		json={"username": target_payload["username"], "password": target_payload["password"]},
	)
	assert login_response.status_code == 401


async def test_deactivated_user_with_valid_token_returns_401(client: AsyncClient) -> None:
	_, target_token = await register_and_login(client)
	_, admin_token = await register_admin_and_login(client)
	target_id = (await client.get("/users/me", headers=auth_headers(target_token))).json()["id"]

	deactivate_response = await client.delete(f"/users/{target_id}", headers=auth_headers(admin_token))
	assert deactivate_response.status_code == 204

	me_response = await client.get("/users/me", headers=auth_headers(target_token))
	assert me_response.status_code == 401


async def test_demoted_admin_with_valid_token_returns_403(client: AsyncClient) -> None:
	admin_payload, admin_token = await register_admin_and_login(client)
	_, super_admin_token = await register_admin_and_login(client)
	admin_id = (await client.get("/users/me", headers=auth_headers(admin_token))).json()["id"]

	demote_response = await client.patch(
		f"/users/{admin_id}",
		json={"role": "user"},
		headers=auth_headers(super_admin_token),
	)
	assert demote_response.status_code == 200

	delete_response = await client.delete(
		f"/users/{admin_id}",
		headers=auth_headers(admin_token),
	)
	assert delete_response.status_code == 403

	login_response = await client.post(
		"/auth/login",
		json={"username": admin_payload["username"], "password": admin_payload["password"]},
	)
	assert login_response.status_code == 200
	assert login_response.json()["access_token"]
