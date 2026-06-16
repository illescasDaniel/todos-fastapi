import pytest
from httpx import AsyncClient

from factories import user_signup_payload
from integration.api.helpers import auth_headers, register_admin_and_login, register_and_login
from todos_app.domain.ids import UNKNOWN_ID


pytestmark = pytest.mark.integration


async def test_given_authenticated_user_when_getting_me_then_returns_profile(client: AsyncClient) -> None:
	# given
	user = await register_and_login(client)

	# when
	response = await client.get("/users/me", headers=auth_headers(user.token))

	# then
	assert response.status_code == 200
	body = response.json()
	assert body["username"] == user.payload["username"]
	assert body["email"] == user.payload["email"]


async def test_given_authenticated_user_when_replacing_me_then_updates_profile(client: AsyncClient) -> None:
	# given
	user = await register_and_login(client)

	# when
	response = await client.put(
		"/users/me",
		json={
			"email": "updated@example.com",
			"username": "updated-user",
			"first_name": "Updated",
			"last_name": "Name",
		},
		headers=auth_headers(user.token),
	)

	# then
	assert response.status_code == 200
	body = response.json()
	assert body["email"] == "updated@example.com"
	assert body["first_name"] == "Updated"


async def test_given_authenticated_user_when_patching_me_then_updates_partial_profile(
	client: AsyncClient,
) -> None:
	# given
	user = await register_and_login(client)

	# when
	response = await client.patch(
		"/users/me",
		json={"last_name": "Patched"},
		headers=auth_headers(user.token),
	)

	# then
	assert response.status_code == 200
	assert response.json()["last_name"] == "Patched"


async def test_given_signup_payload_with_admin_role_when_creating_user_then_returns_422(
	client: AsyncClient,
) -> None:
	# given
	payload = user_signup_payload(role="admin")

	# when
	response = await client.post("/users", json=payload)

	# then
	assert response.status_code == 422


async def test_given_valid_signup_payload_when_creating_user_then_assigns_user_role(
	client: AsyncClient,
) -> None:
	# given
	payload = user_signup_payload()

	# when
	response = await client.post("/users", json=payload)

	# then
	assert response.status_code == 201
	assert response.json()["role"] == "user"


async def test_given_admin_and_target_user_when_replacing_user_then_updates_profile(
	client: AsyncClient,
) -> None:
	# given
	target = await register_and_login(client)
	admin = await register_admin_and_login(client)

	# when
	response = await client.put(
		f"/users/{target.user_id}",
		json={
			"email": target.payload["email"],
			"username": target.payload["username"],
			"first_name": "Admin",
			"last_name": "Updated",
			"role": "user",
			"is_active": True,
		},
		headers=auth_headers(admin.token),
	)

	# then
	assert response.status_code == 200
	assert response.json()["first_name"] == "Admin"


async def test_given_admin_and_target_user_when_patching_user_role_then_promotes_to_admin(
	client: AsyncClient,
) -> None:
	# given
	target = await register_and_login(client)
	admin = await register_admin_and_login(client)

	# when
	response = await client.patch(
		f"/users/{target.user_id}",
		json={"role": "admin"},
		headers=auth_headers(admin.token),
	)

	# then
	assert response.status_code == 200
	assert response.json()["role"] == "admin"


async def test_given_non_admin_user_when_deleting_another_user_then_returns_403(
	client: AsyncClient,
) -> None:
	# given
	owner = await register_and_login(client)
	other = await register_and_login(client)

	# when
	response = await client.delete(f"/users/{owner.user_id}", headers=auth_headers(other.token))

	# then
	assert response.status_code == 403


async def test_given_admin_and_active_user_when_soft_deleting_user_then_returns_204(
	client: AsyncClient,
) -> None:
	# given
	target = await register_and_login(client)
	admin = await register_admin_and_login(client)

	# when
	response = await client.delete(f"/users/{target.user_id}", headers=auth_headers(admin.token))

	# then
	assert response.status_code == 204


async def test_given_soft_deleted_user_when_logging_in_then_returns_401(client: AsyncClient) -> None:
	# given
	target = await register_and_login(client)
	admin = await register_admin_and_login(client)
	await client.delete(f"/users/{target.user_id}", headers=auth_headers(admin.token))

	# when
	login_response = await client.post(
		"/auth/login",
		json={"username": target.payload["username"], "password": target.payload["password"]},
	)

	# then
	assert login_response.status_code == 401


async def test_given_admin_and_active_user_when_hard_deleting_user_then_returns_204(
	client: AsyncClient,
) -> None:
	# given
	target = await register_and_login(client)
	admin = await register_admin_and_login(client)

	# when
	response = await client.delete(
		f"/users/{target.user_id}",
		params={"hard": "true"},
		headers=auth_headers(admin.token),
	)

	# then
	assert response.status_code == 204


async def test_given_hard_deleted_user_with_old_token_when_getting_me_then_returns_401(
	client: AsyncClient,
) -> None:
	# given
	target = await register_and_login(client)
	admin = await register_admin_and_login(client)
	await client.delete(
		f"/users/{target.user_id}",
		params={"hard": "true"},
		headers=auth_headers(admin.token),
	)

	# when
	me_response = await client.get("/users/me", headers=auth_headers(target.token))

	# then
	assert me_response.status_code == 401


async def test_given_admin_and_unknown_user_id_when_patching_user_then_returns_404(
	client: AsyncClient,
) -> None:
	# given
	admin = await register_admin_and_login(client)

	# when
	response = await client.patch(
		f"/users/{UNKNOWN_ID}",
		json={"first_name": "Ghost"},
		headers=auth_headers(admin.token),
	)

	# then
	assert response.status_code == 404


async def test_given_existing_email_when_signing_up_again_then_returns_generic_400(client: AsyncClient) -> None:
	"""M2: duplicate signup returns 400 with generic message to prevent account enumeration."""
	# given
	payload = user_signup_payload()
	first = await client.post("/users", json=payload)
	assert first.status_code == 201
	duplicate = user_signup_payload(email=payload["email"])

	# when
	second = await client.post("/users", json=duplicate)

	# then
	assert second.status_code == 400
	detail = second.json()["detail"][0]
	assert detail["msg"] == "Unable to create account"
	assert "ctx" not in detail or detail.get("ctx") is None
