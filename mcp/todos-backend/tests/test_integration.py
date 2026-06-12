import json
import os

import httpx
import pytest

from todos_mcp.client import ApiClient
from todos_mcp.config import Settings


@pytest.mark.integration
@pytest.mark.asyncio
async def test_live_health() -> None:
    base_url = os.environ.get("TODOS_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{base_url}/health")
    except httpx.RequestError:
        pytest.skip("API not reachable")

    if response.status_code != 200:
        pytest.skip("API not healthy")

    settings = Settings(api_base_url=base_url, repo_root=__import__("pathlib").Path("/tmp"))
    api = ApiClient(settings)
    result = json.loads(await api.request("GET", "/health"))
    assert result["ok"] is True
    assert result["data"]["status"] == "ok"
