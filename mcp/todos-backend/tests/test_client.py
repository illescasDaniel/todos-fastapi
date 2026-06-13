import json

import httpx
import pytest

from todos_mcp.client import ApiClient
from todos_mcp.config import Settings


@pytest.fixture
def settings() -> Settings:
	return Settings(api_base_url="http://testserver", repo_root=__import__("pathlib").Path("/tmp/repo"))


@pytest.fixture
def client(settings: Settings) -> ApiClient:
	return ApiClient(settings)


def _patch_async_client(monkeypatch: pytest.MonkeyPatch, transport: httpx.MockTransport) -> None:
	original_async_client = httpx.AsyncClient

	def patched_async_client(*args, **kwargs):
		kwargs["transport"] = transport
		return original_async_client(*args, **kwargs)

	monkeypatch.setattr(httpx, "AsyncClient", patched_async_client)


@pytest.mark.asyncio
async def test_request_success(client: ApiClient, monkeypatch: pytest.MonkeyPatch) -> None:
	async def handler(request: httpx.Request) -> httpx.Response:
		assert request.url.path == "/health"
		return httpx.Response(200, json={"status": "ok"})

	_patch_async_client(monkeypatch, httpx.MockTransport(handler))

	response = await client.request("GET", "/health")
	payload = json.loads(response)
	assert payload["ok"] is True
	assert payload["status"] == 200
	assert payload["data"] == {"status": "ok"}


@pytest.mark.asyncio
async def test_request_error_status(client: ApiClient, monkeypatch: pytest.MonkeyPatch) -> None:
	async def handler(request: httpx.Request) -> httpx.Response:
		return httpx.Response(401, json={"detail": "Invalid credentials"})

	_patch_async_client(monkeypatch, httpx.MockTransport(handler))

	response = await client.request(
		"POST",
		"/auth/login",
		json_body={"username": "x", "password": "wrongpass"},
	)
	payload = json.loads(response)
	assert payload["ok"] is False
	assert payload["status"] == 401
	assert payload["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_request_204(client: ApiClient, monkeypatch: pytest.MonkeyPatch) -> None:
	async def handler(request: httpx.Request) -> httpx.Response:
		return httpx.Response(204)

	_patch_async_client(monkeypatch, httpx.MockTransport(handler))

	response = await client.request("DELETE", "/todos/abc", access_token="token")
	payload = json.loads(response)
	assert payload["ok"] is True
	assert payload["status"] == 204
	assert payload["data"] is None
