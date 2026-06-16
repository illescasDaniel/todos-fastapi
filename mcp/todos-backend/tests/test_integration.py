import json

import httpx
import pytest

from todos_mcp.client import ApiClient
from todos_mcp.config import load_settings


@pytest.mark.integration
@pytest.mark.asyncio
async def test_live_health(monkeypatch: pytest.MonkeyPatch) -> None:
	repo_root = __import__("pathlib").Path(__file__).resolve().parents[3]
	monkeypatch.setenv("ENV_PROFILE", "test")
	monkeypatch.setenv("TODOS_REPO_ROOT", str(repo_root))
	settings = load_settings()
	base_url = settings.api_base_url
	try:
		async with httpx.AsyncClient(timeout=2.0) as client:
			response = await client.get(f"{base_url}/health")
	except httpx.RequestError:
		pytest.skip("API not reachable")

	if response.status_code != 200:
		pytest.skip("API not healthy")

	api = ApiClient(settings)
	result = json.loads(await api.request("GET", "/health"))
	assert result["ok"] is True
	assert result["data"]["status"] == "ok"
