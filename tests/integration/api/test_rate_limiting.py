"""Integration tests for H2 rate limiting on /auth/login and POST /users."""

import pytest
from httpx import AsyncClient

from factories import user_signup_payload


pytestmark = pytest.mark.integration


async def test_rate_limiter_middleware_is_installed() -> None:
	"""H2: verifies the SlowAPIMiddleware is registered on the app."""
	from slowapi.middleware import SlowAPIMiddleware

	from todos_app.main import app

	middleware_classes = [m.cls if hasattr(m, "cls") else m for m in app.user_middleware]
	assert SlowAPIMiddleware in middleware_classes


async def test_login_rate_limit_returns_429(client: AsyncClient) -> None:
	"""H2: /auth/login returns 429 after exceeding 20 requests per minute."""
	from todos_app.core.rate_limiting import limiter

	# Override the key function to return a deterministic IP for this test only.
	original_key_func = limiter._key_func  # pyright: ignore[reportAttributeAccessIssue]
	limiter._key_func = lambda req: "10.99.99.1"  # pyright: ignore[reportAttributeAccessIssue]
	try:
		responses = []
		for _ in range(21):
			r = await client.post(
				"/auth/login",
				json={"username": "test_rl", "password": "testpass1"},
			)
			responses.append(r.status_code)
	finally:
		limiter._key_func = original_key_func  # pyright: ignore[reportAttributeAccessIssue]

	assert 429 in responses, f"Expected a 429 within 21 requests, got: {responses}"


async def test_signup_rate_limit_returns_429(client: AsyncClient) -> None:
	"""H2: POST /users returns 429 after exceeding 10 requests per minute."""
	from todos_app.core.rate_limiting import limiter

	original_key_func = limiter._key_func  # pyright: ignore[reportAttributeAccessIssue]
	limiter._key_func = lambda req: "10.99.99.2"  # pyright: ignore[reportAttributeAccessIssue]
	try:
		responses = []
		for _ in range(11):
			r = await client.post("/users", json=user_signup_payload())
			responses.append(r.status_code)
	finally:
		limiter._key_func = original_key_func  # pyright: ignore[reportAttributeAccessIssue]

	assert 429 in responses, f"Expected a 429 within 11 requests, got: {responses}"
