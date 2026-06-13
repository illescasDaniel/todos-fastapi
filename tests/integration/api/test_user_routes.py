import pytest
from httpx import AsyncClient

from factories import user_signup_payload
from integration.api.helpers import auth_headers, register_admin_and_login, register_and_login
from todos_app.domain.ids import UNKNOWN_ID


pytestmark = pytest.mark.integration


async def test_get_me_returns_authenticated_user(client: AsyncClient) -> None:
	payload, token = await register_and_login(client)
	response = await client.get("/users/me", headers=auth_headers(token))
	assert response.status_code == 200
	body = response.json()
	assert body["username"] == payload["username"]
	assert body["email"] == payload["email"]


async def test_replace_me_updates_profile(client: AsyncClient) -> None:
	_, token = await register_and_login(client)
	response = await client.put(
		"/users/me",
		json={
			"email": "updated@example.com",
			"username": "updated-user",
			"first_name": "Updated",
			"last_name": "Name",
		},
		headers=auth_headers(token),
	)
	assert response.status_code == 200
	body = response.json()
	assert body["email"] == "updated@example.com"
	assert body["first_name"] == "Updated"


async def test_patch_me_updates_partial_profile(client: AsyncClient) -> None:
	_, token = await register_and_login(client)
	response = await client.patch(
		"/users/me",
		json={"last_name": "Patched"},
		headers=auth_headers(token),
	)
	assert response.status_code == 200
	assert response.json()["last_name"] == "Patched"


async def test_signup_rejects_client_controlled_role(client: AsyncClient) -> None:
	payload = user_signup_payload(role="admin")
	response = await client.post("/users", json=payload)
	assert response.status_code == 422


async def test_signup_always_creates_user_role(client: AsyncClient) -> None:
	payload = user_signup_payload()
	response = await client.post("/users", json=payload)
	assert response.status_code == 201
	assert response.json()["role"] == "user"


async def test_admin_replace_user(client: AsyncClient) -> None:
	target_payload, target_token = await register_and_login(client)
	_, admin_token = await register_admin_and_login(client)
	target_id = (await client.get("/users/me", headers=auth_headers(target_token))).json()["id"]

	response = await client.put(
		f"/users/{target_id}",
		json={
			"email": target_payload["email"],
			"username": target_payload["username"],
			"first_name": "Admin",
			"last_name": "Updated",
			"role": "user",
			"is_active": True,
		},
		headers=auth_headers(admin_token),
	)
	assert response.status_code == 200
	assert response.json()["first_name"] == "Admin"


async def test_admin_patch_user(client: AsyncClient) -> None:
	_, target_token = await register_and_login(client)
	_, admin_token = await register_admin_and_login(client)
	target_id = (await client.get("/users/me", headers=auth_headers(target_token))).json()["id"]

	response = await client.patch(
		f"/users/{target_id}",
		json={"role": "admin"},
		headers=auth_headers(admin_token),
	)
	assert response.status_code == 200
	assert response.json()["role"] == "admin"


async def test_non_admin_cannot_delete_user(client: AsyncClient) -> None:
	_, owner_token = await register_and_login(client)
	_, other_token = await register_and_login(client)
	owner_id = (await client.get("/users/me", headers=auth_headers(owner_token))).json()["id"]

	response = await client.delete(f"/users/{owner_id}", headers=auth_headers(other_token))
	assert response.status_code == 403


async def test_admin_soft_delete_deactivates_user(client: AsyncClient) -> None:
	target_payload, target_token = await register_and_login(client)
	_, admin_token = await register_admin_and_login(client)
	target_id = (await client.get("/users/me", headers=auth_headers(target_token))).json()["id"]

	response = await client.delete(f"/users/{target_id}", headers=auth_headers(admin_token))
	assert response.status_code == 204

	login_response = await client.post(
		"/auth/login",
		json={"username": target_payload["username"], "password": target_payload["password"]},
	)
	assert login_response.status_code == 401


async def test_admin_hard_delete_removes_user(client: AsyncClient) -> None:
	_, target_token = await register_and_login(client)
	_, admin_token = await register_admin_and_login(client)
	target_id = (await client.get("/users/me", headers=auth_headers(target_token))).json()["id"]

	response = await client.delete(
		f"/users/{target_id}",
		params={"hard": "true"},
		headers=auth_headers(admin_token),
	)
	assert response.status_code == 204

	me_response = await client.get("/users/me", headers=auth_headers(target_token))
	assert me_response.status_code == 401


async def test_admin_update_missing_user_returns_404(client: AsyncClient) -> None:
	_, admin_token = await register_admin_and_login(client)
	response = await client.patch(
		f"/users/{UNKNOWN_ID}",
		json={"first_name": "Ghost"},
		headers=auth_headers(admin_token),
	)
	assert response.status_code == 404


async def test_duplicate_email_returns_400(client: AsyncClient) -> None:
	"""M2: duplicate signup returns 400 with generic message to prevent account enumeration."""
	payload = user_signup_payload()
	first = await client.post("/users", json=payload)
	assert first.status_code == 201

	duplicate = user_signup_payload(email=payload["email"])
	second = await client.post("/users", json=duplicate)
	assert second.status_code == 400
	detail = second.json()["detail"][0]
	assert detail["msg"] == "Unable to create account"
	assert "ctx" not in detail or detail.get("ctx") is None
