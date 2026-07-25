from collections.abc import AsyncIterator

import pytest
from sqlalchemy import text

from todos_app.shared.adapters.persistence.database import engine
from todos_app.shared.rate_limiting import limiter


@pytest.fixture(autouse=True)
async def reset_integration_db(initialized_db: None) -> AsyncIterator[None]:  # pyright: ignore[reportUnusedParameter]
	async with engine.begin() as conn:
		await conn.execute(text("SET LOCAL synchronous_commit = off"))
		await conn.execute(text("DELETE FROM todos"))
		await conn.execute(text("DELETE FROM users"))
	storage = getattr(limiter, "_storage", None)
	if storage is not None and hasattr(storage, "reset"):
		storage.reset()
	yield
