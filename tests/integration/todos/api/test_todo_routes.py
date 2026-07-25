import pytest
from httpx import AsyncClient

from factories import todo_create_payload
from integration.api.helpers import auth_headers, register_and_login


pytestmark = pytest.mark.integration


async def _create_todo(
	client: AsyncClient,
	*,
	headers: dict[str, str],
	title: str,
	**payload_overrides: object,
) -> str:
	create_response = await client.post(
		"/todos",
		json=todo_create_payload(title=title, **payload_overrides),
		headers=headers,
	)
	assert create_response.status_code == 201
	return create_response.json()["id"]


async def test_given_authenticated_user_when_creating_todo_then_returns_201(client: AsyncClient) -> None:
	# given
	user = await register_and_login(client)
	headers = auth_headers(user.token)

	# when
	create_response = await client.post(
		"/todos",
		json=todo_create_payload(title="My task"),
		headers=headers,
	)

	# then
	assert create_response.status_code == 201
	assert create_response.json()["id"]


async def test_given_owned_todo_when_listing_todos_then_includes_item(client: AsyncClient) -> None:
	# given
	user = await register_and_login(client)
	headers = auth_headers(user.token)
	await _create_todo(client, headers=headers, title="My task")

	# when
	list_response = await client.get("/todos", headers=headers)

	# then
	assert list_response.status_code == 200
	items = list_response.json()["items"]
	assert len(items) == 1
	assert items[0]["title"] == "My task"


async def test_given_owned_todo_when_getting_by_id_then_returns_todo(client: AsyncClient) -> None:
	# given
	user = await register_and_login(client)
	headers = auth_headers(user.token)
	todo_id = await _create_todo(client, headers=headers, title="My task")

	# when
	get_response = await client.get(f"/todos/{todo_id}", headers=headers)

	# then
	assert get_response.status_code == 200
	assert get_response.json()["id"] == todo_id


async def test_given_owned_todo_when_putting_then_updates_todo(client: AsyncClient) -> None:
	# given
	user = await register_and_login(client)
	headers = auth_headers(user.token)
	todo_id = await _create_todo(client, headers=headers, title="Original")

	# when
	put_response = await client.put(
		f"/todos/{todo_id}",
		json=todo_create_payload(title="Replaced", completed=True),
		headers=headers,
	)

	# then
	assert put_response.status_code == 200
	assert put_response.json()["title"] == "Replaced"
	assert put_response.json()["completed"] is True


async def test_given_owned_todo_when_patching_then_partially_updates(client: AsyncClient) -> None:
	# given
	user = await register_and_login(client)
	headers = auth_headers(user.token)
	todo_id = await _create_todo(client, headers=headers, title="Original")

	# when
	patch_response = await client.patch(
		f"/todos/{todo_id}",
		json={"title": "Patched"},
		headers=headers,
	)

	# then
	assert patch_response.status_code == 200
	assert patch_response.json()["title"] == "Patched"


async def test_given_deleted_todo_when_getting_by_id_then_returns_404(client: AsyncClient) -> None:
	# given
	user = await register_and_login(client)
	headers = auth_headers(user.token)
	todo_id = await _create_todo(client, headers=headers, title="Original")
	await client.delete(f"/todos/{todo_id}", headers=headers)

	# when
	get_response = await client.get(f"/todos/{todo_id}", headers=headers)

	# then
	assert get_response.status_code == 404


async def test_given_three_todos_when_listing_first_page_then_returns_two_with_cursor(
	client: AsyncClient,
) -> None:
	# given
	user = await register_and_login(client)
	headers = auth_headers(user.token)
	for title in ("First", "Second", "Third"):
		await _create_todo(client, headers=headers, title=title)

	# when
	first_page = await client.get("/todos", params={"limit": 2}, headers=headers)

	# then
	assert first_page.status_code == 200
	body = first_page.json()
	assert len(body["items"]) == 2
	assert body["next_last_id"] is not None


async def test_given_three_todos_when_listing_second_page_then_returns_remaining_item(
	client: AsyncClient,
) -> None:
	# given
	user = await register_and_login(client)
	headers = auth_headers(user.token)
	for title in ("First", "Second", "Third"):
		await _create_todo(client, headers=headers, title=title)
	first_page = await client.get("/todos", params={"limit": 2}, headers=headers)
	next_last_id = first_page.json()["next_last_id"]

	# when
	second_page = await client.get(
		"/todos",
		params={"limit": 2, "last_id": next_last_id},
		headers=headers,
	)

	# then
	assert second_page.status_code == 200
	second_body = second_page.json()
	assert len(second_body["items"]) == 1
	assert second_body["next_last_id"] is None


async def test_given_regular_user_and_other_owner_when_putting_with_owner_change_then_returns_403(
	client: AsyncClient,
) -> None:
	# given
	user_a = await register_and_login(client)
	user_b = await register_and_login(client)
	headers_a = auth_headers(user_a.token)
	todo_id = await _create_todo(client, headers=headers_a, title="Mine")

	# when
	response = await client.put(
		f"/todos/{todo_id}",
		json={**todo_create_payload(title="Stolen"), "owner_id": str(user_b.user_id)},
		headers=headers_a,
	)

	# then
	assert response.status_code == 403


async def test_given_authenticated_user_when_creating_todo_without_optionals_then_persists_null_fields(
	client: AsyncClient,
) -> None:
	# given
	user = await register_and_login(client)
	headers = auth_headers(user.token)

	# when
	response = await client.post(
		"/todos",
		json={"title": "Title only", "completed": False},
		headers=headers,
	)

	# then
	assert response.status_code == 201
	body = response.json()
	assert body["title"] == "Title only"
	assert body["description"] is None
	assert body["priority"] is None


@pytest.mark.parametrize(
	"payload",
	[
		{"title": "", "completed": False},
		{"title": "Valid", "description": "", "completed": False},
		{"title": "Valid", "priority": "", "completed": False},
	],
)
async def test_given_empty_string_field_when_creating_todo_then_returns_422(
	client: AsyncClient,
	payload: dict[str, object],
) -> None:
	# given
	user = await register_and_login(client)
	headers = auth_headers(user.token)

	# when
	response = await client.post("/todos", json=payload, headers=headers)

	# then
	assert response.status_code == 422


async def test_given_todo_with_description_when_patching_description_to_null_then_clears_field(
	client: AsyncClient,
) -> None:
	# given
	user = await register_and_login(client)
	headers = auth_headers(user.token)
	todo_id = await _create_todo(client, headers=headers, title="With description")

	# when
	patch_response = await client.patch(
		f"/todos/{todo_id}",
		json={"description": None},
		headers=headers,
	)

	# then
	assert patch_response.status_code == 200
	assert patch_response.json()["description"] is None


async def test_given_owned_todo_when_patching_empty_title_then_returns_422(client: AsyncClient) -> None:
	# given
	user = await register_and_login(client)
	headers = auth_headers(user.token)
	todo_id = await _create_todo(client, headers=headers, title="Keep")

	# when
	patch_response = await client.patch(
		f"/todos/{todo_id}",
		json={"title": ""},
		headers=headers,
	)

	# then
	assert patch_response.status_code == 422


async def test_given_other_users_todo_when_getting_by_id_then_returns_404(client: AsyncClient) -> None:
	# given
	owner = await register_and_login(client)
	other = await register_and_login(client)
	owner_headers = auth_headers(owner.token)
	todo_id = await _create_todo(client, headers=owner_headers, title="Private")
	other_headers = auth_headers(other.token)

	# when
	get_response = await client.get(f"/todos/{todo_id}", headers=other_headers)

	# then
	assert get_response.status_code == 404
