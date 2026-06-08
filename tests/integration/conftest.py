from collections.abc import AsyncIterator

import pytest
from sqlalchemy import text

from todos_app.infrastructure.persistence.database import engine


@pytest.fixture(autouse=True)
async def reset_integration_db(initialized_db: None) -> AsyncIterator[None]:  # pyright: ignore[reportUnusedParameter]
	async with engine.begin() as conn:
		await conn.execute(text("TRUNCATE TABLE todos, users RESTART IDENTITY CASCADE"))
	yield
