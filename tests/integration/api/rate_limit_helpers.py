from collections.abc import Generator
from contextlib import contextmanager

from slowapi.wrappers import Limit, LimitGroup

from todos_app.core.rate_limiting import limiter


LOGIN_ROUTE_KEY = "todos_app.api.auth.router.login"
CREATE_USER_ROUTE_KEY = "todos_app.api.users.router.create_user"


def _limits_for(limit_value: str) -> list[Limit]:
	return list(
		LimitGroup(
			limit_value,
			limiter._key_func,  # pyright: ignore[reportPrivateUsage]
			None,
			False,
			None,
			None,
			None,
			1,
			False,
		)
	)


@contextmanager
def lowered_route_rate_limit(endpoint_key: str, limit_value: str) -> Generator[None]:
	original = list(limiter._route_limits.get(endpoint_key, []))  # pyright: ignore[reportPrivateUsage]
	limiter._route_limits[endpoint_key] = _limits_for(limit_value)  # pyright: ignore[reportPrivateUsage]
	try:
		yield
	finally:
		if original:
			limiter._route_limits[endpoint_key] = original  # pyright: ignore[reportPrivateUsage]
		else:
			limiter._route_limits.pop(endpoint_key, None)  # pyright: ignore[reportPrivateUsage]
