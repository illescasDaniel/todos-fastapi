import json
from collections.abc import Iterator
from uuid import uuid7

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select

from fakes.idempotency_store import FakeIdempotencyStore
from integration.api.helpers import auth_headers, register_and_login
from todos_app.core.idempotency import build_scope_key, compute_request_fingerprint
from todos_app.core.idempotency_factory import set_idempotency_store_factory
from todos_app.infrastructure.persistence.database import AsyncSessionLocal
from todos_app.infrastructure.persistence.todos.orm import TodoModel


pytestmark = pytest.mark.integration

_FAKE_IDEMPOTENCY_STORE = FakeIdempotencyStore()


@pytest.fixture(scope="module", autouse=True)
def wire_fake_idempotency_store() -> Iterator[None]:
	set_idempotency_store_factory(lambda: _FAKE_IDEMPOTENCY_STORE)
	yield
	set_idempotency_store_factory(None)


@pytest.fixture(autouse=True)
def clear_fake_idempotency_store() -> None:
	_FAKE_IDEMPOTENCY_STORE.clear()


async def _count_todos() -> int:
	async with AsyncSessionLocal() as session:
		result = await session.execute(select(func.count()).select_from(TodoModel))
		return int(result.scalar_one())


async def test_given_same_idempotency_key_when_creating_todo_twice_then_replays_response_and_single_row(
	client: AsyncClient,
) -> None:
	user = await register_and_login(client)
	idempotency_key = str(uuid7())
	headers = {**auth_headers(user.token), "Idempotency-Key": idempotency_key}
	body = {"title": "Retry-safe todo", "completed": False}
	before_count = await _count_todos()

	first = await client.post("/todos", json=body, headers=headers)
	second = await client.post("/todos", json=body, headers=headers)

	assert first.status_code == 201
	assert second.status_code == 201
	assert first.json() == second.json()
	assert await _count_todos() == before_count + 1


async def test_given_same_idempotency_key_when_body_differs_then_returns_422(client: AsyncClient) -> None:
	user = await register_and_login(client)
	idempotency_key = str(uuid7())
	headers = {**auth_headers(user.token), "Idempotency-Key": idempotency_key}

	first = await client.post("/todos", json={"title": "First body", "completed": False}, headers=headers)
	second = await client.post("/todos", json={"title": "Second body", "completed": False}, headers=headers)

	assert first.status_code == 201
	assert second.status_code == 422
	assert second.json()["detail"] == "Idempotency-Key was already used with a different request"


async def test_given_in_progress_record_when_replaying_request_then_returns_409(client: AsyncClient) -> None:
	user = await register_and_login(client)
	idempotency_key = str(uuid7())
	body = {"title": "Busy todo", "completed": False}
	scope_key = build_scope_key(user_id=user.user_id, idempotency_key=idempotency_key)
	fingerprint = compute_request_fingerprint(
		method="POST",
		path="/todos",
		query="",
		body=json.dumps(body).encode(),
	)
	_FAKE_IDEMPOTENCY_STORE.seed_in_progress(scope_key, fingerprint=fingerprint)
	headers = {**auth_headers(user.token), "Idempotency-Key": idempotency_key}

	response = await client.post("/todos", json=body, headers=headers)

	assert response.status_code == 409
	assert response.json()["detail"] == "A request with this Idempotency-Key is already in progress"


async def test_given_completed_delete_when_replaying_delete_then_returns_204_without_404(
	client: AsyncClient,
) -> None:
	user = await register_and_login(client)
	create = await client.post(
		"/todos",
		json={"title": "Delete me", "completed": False},
		headers=auth_headers(user.token),
	)
	assert create.status_code == 201
	todo_id = create.json()["id"]
	idempotency_key = str(uuid7())
	headers = {**auth_headers(user.token), "Idempotency-Key": idempotency_key}

	first = await client.delete(f"/todos/{todo_id}", headers=headers)
	second = await client.delete(f"/todos/{todo_id}", headers=headers)

	assert first.status_code == 204
	assert second.status_code == 204
