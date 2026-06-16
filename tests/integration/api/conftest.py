from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from todos_app.main import app


@pytest.fixture(scope="module")
async def client(initialized_db: None) -> AsyncIterator[AsyncClient]:  # pyright: ignore[reportUnusedParameter]
	transport = ASGITransport(app=app)
	async with AsyncClient(transport=transport, base_url="http://test") as ac:
		yield ac
