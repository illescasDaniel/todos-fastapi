from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from todos_app.auth.adapters.api.router import router as auth_router
from todos_app.idempotency.adapters.api.middleware import idempotency_middleware
from todos_app.runtime.exceptions import register_exception_handlers
from todos_app.shared.adapters.api.health.router import router as health_router
from todos_app.shared.logging import configure_logger
from todos_app.shared.rate_limiting import limiter
from todos_app.shared.settings import get_settings
from todos_app.todos.adapters.api.router import router as todos_router
from todos_app.users.adapters.api.router import router as users_router


def create_app() -> FastAPI:
	settings = get_settings()
	app = FastAPI(
		docs_url="/docs" if settings.exposes_api_docs() else None,
		redoc_url="/redoc" if settings.exposes_api_docs() else None,
		openapi_url="/openapi.json" if settings.exposes_api_docs() else None,
	)
	configure_logger()
	register_exception_handlers(app)

	app.state.limiter = limiter
	app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # pyright: ignore[reportArgumentType]
	app.add_middleware(SlowAPIMiddleware)

	max_body_size = settings.api.body_max_bytes

	@app.middleware("http")
	async def limit_body_size(  # pyright: ignore[reportUnusedFunction]
		request: Request, call_next: Callable[[Request], Awaitable[Response]]
	) -> Response:
		content_length = request.headers.get("content-length")
		if content_length is not None and int(content_length) > max_body_size:
			return JSONResponse(
				status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
				content={"detail": "Request body too large"},
			)
		return await call_next(request)

	@app.middleware("http")
	async def idempotency(  # pyright: ignore[reportUnusedFunction]
		request: Request, call_next: Callable[[Request], Awaitable[Response]]
	) -> Response:
		return await idempotency_middleware(request, call_next)

	async def _validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
		assert isinstance(exc, RequestValidationError)
		if settings.is_local():
			from fastapi.exception_handlers import request_validation_exception_handler

			return await request_validation_exception_handler(request, exc)  # pyright: ignore[reportReturnType]
		return JSONResponse(
			status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
			content={"detail": "Invalid request"},
		)

	app.add_exception_handler(RequestValidationError, _validation_error_handler)  # pyright: ignore[reportArgumentType]

	app.include_router(health_router)
	app.include_router(todos_router)
	app.include_router(users_router)
	app.include_router(auth_router)
	return app
