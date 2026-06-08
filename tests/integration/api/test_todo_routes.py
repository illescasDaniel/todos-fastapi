import pytest
from httpx import AsyncClient

from factories import todo_create_payload
from integration.api.helpers import auth_headers, register_and_login


pytestmark = pytest.mark.integration


async def test_todo_crud_flow(client: AsyncClient) -> None:
	_, token = await register_and_login(client)
	headers = auth_headers(token)

	create_response = await client.post(
		"/todos",
		json=todo_create_payload(title="My task"),
		headers=headers,
	)
	assert create_response.status_code == 201
	created = create_response.json()
	todo_id = created["id"]

	list_response = await client.get("/todos", headers=headers)
	assert list_response.status_code == 200
	items = list_response.json()["items"]
	assert len(items) == 1
	assert items[0]["title"] == "My task"

	get_response = await client.get(f"/todos/{todo_id}", headers=headers)
	assert get_response.status_code == 200
	assert get_response.json()["id"] == todo_id


async def test_todo_put_patch_delete_flow(client: AsyncClient) -> None:
	_, token = await register_and_login(client)
	headers = auth_headers(token)

	create_response = await client.post(
		"/todos",
		json=todo_create_payload(title="Original"),
		headers=headers,
	)
	assert create_response.status_code == 201
	todo_id = create_response.json()["id"]

	put_response = await client.put(
		f"/todos/{todo_id}",
		json=todo_create_payload(title="Replaced", completed=True),
		headers=headers,
	)
	assert put_response.status_code == 200
	assert put_response.json()["title"] == "Replaced"
	assert put_response.json()["completed"] is True

	patch_response = await client.patch(
		f"/todos/{todo_id}",
		json={"title": "Patched"},
		headers=headers,
	)
	assert patch_response.status_code == 200
	assert patch_response.json()["title"] == "Patched"

	delete_response = await client.delete(f"/todos/{todo_id}", headers=headers)
	assert delete_response.status_code == 204

	get_response = await client.get(f"/todos/{todo_id}", headers=headers)
	assert get_response.status_code == 404


async def test_todo_list_pagination(client: AsyncClient) -> None:
	_, token = await register_and_login(client)
	headers = auth_headers(token)

	for title in ("First", "Second", "Third"):
		response = await client.post(
			"/todos",
			json=todo_create_payload(title=title),
			headers=headers,
		)
		assert response.status_code == 201

	first_page = await client.get("/todos", params={"limit": 2}, headers=headers)
	assert first_page.status_code == 200
	body = first_page.json()
	assert len(body["items"]) == 2
	assert body["next_last_id"] is not None

	second_page = await client.get(
		"/todos",
		params={"limit": 2, "last_id": body["next_last_id"]},
		headers=headers,
	)
	assert second_page.status_code == 200
	second_body = second_page.json()
	assert len(second_body["items"]) == 1
	assert second_body["next_last_id"] is None


async def test_put_todo_with_owner_change_forbidden_for_regular_user(client: AsyncClient) -> None:
	_, token_a = await register_and_login(client)
	_, token_b = await register_and_login(client)
	headers_a = auth_headers(token_a)
	other_user_id = (await client.get("/users/me", headers=auth_headers(token_b))).json()["id"]

	create_response = await client.post(
		"/todos",
		json=todo_create_payload(title="Mine"),
		headers=headers_a,
	)
	assert create_response.status_code == 201
	todo_id = create_response.json()["id"]

	response = await client.put(
		f"/todos/{todo_id}",
		json={**todo_create_payload(title="Stolen"), "owner_id": other_user_id},
		headers=headers_a,
	)
	assert response.status_code == 403


async def test_create_todo_without_optional_fields(client: AsyncClient) -> None:
	_, token = await register_and_login(client)
	headers = auth_headers(token)

	response = await client.post(
		"/todos",
		json={"title": "Title only", "completed": False},
		headers=headers,
	)
	assert response.status_code == 201
	body = response.json()
	assert body["title"] == "Title only"
	assert body["description"] is None
	assert body["priority"] is None


async def test_create_rejects_empty_string_fields(client: AsyncClient) -> None:
	_, token = await register_and_login(client)
	headers = auth_headers(token)

	for payload in (
		{"title": "", "completed": False},
		{"title": "Valid", "description": "", "completed": False},
		{"title": "Valid", "priority": "", "completed": False},
	):
		response = await client.post("/todos", json=payload, headers=headers)
		assert response.status_code == 422


async def test_patch_null_clears_description(client: AsyncClient) -> None:
	_, token = await register_and_login(client)
	headers = auth_headers(token)

	create_response = await client.post(
		"/todos",
		json=todo_create_payload(title="With description"),
		headers=headers,
	)
	assert create_response.status_code == 201
	todo_id = create_response.json()["id"]
	assert create_response.json()["description"] is not None

	patch_response = await client.patch(
		f"/todos/{todo_id}",
		json={"description": None},
		headers=headers,
	)
	assert patch_response.status_code == 200
	assert patch_response.json()["description"] is None


async def test_patch_rejects_empty_title(client: AsyncClient) -> None:
	_, token = await register_and_login(client)
	headers = auth_headers(token)

	create_response = await client.post(
		"/todos",
		json=todo_create_payload(title="Keep"),
		headers=headers,
	)
	todo_id = create_response.json()["id"]

	patch_response = await client.patch(
		f"/todos/{todo_id}",
		json={"title": ""},
		headers=headers,
	)
	assert patch_response.status_code == 422


async def test_get_other_users_todo_returns_404(client: AsyncClient) -> None:
	_, owner_token = await register_and_login(client)
	_, other_token = await register_and_login(client)

	owner_headers = auth_headers(owner_token)
	create_response = await client.post(
		"/todos",
		json=todo_create_payload(title="Private"),
		headers=owner_headers,
	)
	assert create_response.status_code == 201
	todo_id = create_response.json()["id"]

	other_headers = auth_headers(other_token)
	get_response = await client.get(f"/todos/{todo_id}", headers=other_headers)
	assert get_response.status_code == 404
