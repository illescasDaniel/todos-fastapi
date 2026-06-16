"""Integration tests for H2 rate limiting on /auth/login and POST /users."""

import pytest
from httpx import AsyncClient

from factories import user_signup_payload
from integration.api.rate_limit_helpers import CREATE_USER_ROUTE_KEY, LOGIN_ROUTE_KEY, lowered_route_rate_limit
from todos_app.core.rate_limiting import limiter


pytestmark = pytest.mark.integration


async def test_given_fastapi_app_when_inspecting_middleware_then_includes_slowapi_middleware() -> None:
	"""H2: verifies the SlowAPIMiddleware is registered on the app."""
	# given
	from slowapi.middleware import SlowAPIMiddleware

	from todos_app.main import app

	# when
	middleware_classes = [m.cls if hasattr(m, "cls") else m for m in app.user_middleware]

	# then
	assert SlowAPIMiddleware in middleware_classes


async def test_given_repeated_login_attempts_when_exceeding_route_limit_then_returns_429(
	client: AsyncClient,
) -> None:
	"""H2: /auth/login returns 429 after exceeding the configured per-route limit."""
	# given
	original_key_func = limiter._key_func  # pyright: ignore[reportPrivateUsage]
	limiter._key_func = lambda request: "10.99.99.1"  # pyright: ignore[reportPrivateUsage,reportUnknownLambdaType]

	# when
	try:
		with lowered_route_rate_limit(LOGIN_ROUTE_KEY, "2/minute"):
			responses: list[int] = []
			for _ in range(3):
				response = await client.post(
					"/auth/login",
					json={"username": "test_rl", "password": "testpass1"},
				)
				responses.append(response.status_code)
	finally:
		limiter._key_func = original_key_func  # pyright: ignore[reportPrivateUsage]

	# then
	assert 429 in responses, f"Expected a 429 within 3 requests, got: {responses}"


async def test_given_repeated_signup_attempts_when_exceeding_route_limit_then_returns_429(
	client: AsyncClient,
) -> None:
	"""H2: POST /users returns 429 after exceeding the configured per-route limit."""
	# given
	original_key_func = limiter._key_func  # pyright: ignore[reportPrivateUsage]
	limiter._key_func = lambda request: "10.99.99.2"  # pyright: ignore[reportPrivateUsage,reportUnknownLambdaType]

	# when
	try:
		with lowered_route_rate_limit(CREATE_USER_ROUTE_KEY, "2/minute"):
			responses: list[int] = []
			for _ in range(3):
				response = await client.post("/users", json=user_signup_payload())
				responses.append(response.status_code)
	finally:
		limiter._key_func = original_key_func  # pyright: ignore[reportPrivateUsage]

	# then
	assert 429 in responses, f"Expected a 429 within 3 requests, got: {responses}"
