import pytest
from httpx import AsyncClient

from factories import user_signup_payload
from integration.api.helpers import auth_headers, register_admin_and_login, register_and_login


pytestmark = pytest.mark.integration


async def test_given_registered_user_when_login_with_valid_credentials_then_returns_bearer_token(
	client: AsyncClient,
) -> None:
	# given
	payload = user_signup_payload()
	await client.post("/users", json=payload)

	# when
	login_response = await client.post(
		"/auth/login",
		json={"username": payload["username"], "password": payload["password"]},
	)

	# then
	assert login_response.status_code == 200
	body = login_response.json()
	assert body["access_token"]
	assert body["token_type"] == "bearer"


async def test_given_invalid_credentials_when_logging_in_then_returns_401(client: AsyncClient) -> None:
	# given

	# when
	response = await client.post(
		"/auth/login",
		json={"username": "nobody", "password": "wrongpass"},
	)

	# then
	assert response.status_code == 401


async def test_given_no_bearer_token_when_accessing_protected_route_then_returns_401(
	client: AsyncClient,
) -> None:
	# given

	# when
	response = await client.get("/todos")

	# then
	assert response.status_code == 401


async def test_given_deactivated_user_when_logging_in_then_returns_401(client: AsyncClient) -> None:
	# given
	target = await register_and_login(client)
	admin = await register_admin_and_login(client)
	await client.delete(
		f"/users/{target.user_id}",
		headers=auth_headers(admin.token),
	)

	# when
	login_response = await client.post(
		"/auth/login",
		json={"username": target.payload["username"], "password": target.payload["password"]},
	)

	# then
	assert login_response.status_code == 401


async def test_given_deactivated_user_with_valid_token_when_getting_me_then_returns_401(
	client: AsyncClient,
) -> None:
	# given
	target = await register_and_login(client)
	admin = await register_admin_and_login(client)
	await client.delete(
		f"/users/{target.user_id}",
		headers=auth_headers(admin.token),
	)

	# when
	me_response = await client.get("/users/me", headers=auth_headers(target.token))

	# then
	assert me_response.status_code == 401


async def test_given_demoted_admin_when_deleting_user_then_returns_403(client: AsyncClient) -> None:
	# given
	admin = await register_admin_and_login(client)
	super_admin = await register_admin_and_login(client)
	await client.patch(
		f"/users/{admin.user_id}",
		json={"role": "user"},
		headers=auth_headers(super_admin.token),
	)

	# when
	delete_response = await client.delete(
		f"/users/{admin.user_id}",
		headers=auth_headers(admin.token),
	)

	# then
	assert delete_response.status_code == 403


async def test_given_demoted_admin_when_logging_in_then_returns_new_token(client: AsyncClient) -> None:
	# given
	admin = await register_admin_and_login(client)
	super_admin = await register_admin_and_login(client)
	await client.patch(
		f"/users/{admin.user_id}",
		json={"role": "user"},
		headers=auth_headers(super_admin.token),
	)

	# when
	login_response = await client.post(
		"/auth/login",
		json={"username": admin.payload["username"], "password": admin.payload["password"]},
	)

	# then
	assert login_response.status_code == 200
	assert login_response.json()["access_token"]
