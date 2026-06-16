import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.integration


async def test_given_running_app_when_getting_health_then_returns_ok(client: AsyncClient) -> None:
	# given

	# when
	response = await client.get("/health")

	# then
	assert response.status_code == 200
	assert response.json() == {"status": "ok"}
