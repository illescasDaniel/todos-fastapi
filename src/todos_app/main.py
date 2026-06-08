import uvicorn
from fastapi import FastAPI

from todos_app.api.auth.router import router as auth_router
from todos_app.api.health.router import router as health_router
from todos_app.api.todos.router import router as todos_router
from todos_app.api.users.router import router as users_router
from todos_app.core.exceptions import register_exception_handlers
from todos_app.core.logging import configure_logger
from todos_app.core.settings import get_settings


settings = get_settings()
app = FastAPI(
	docs_url="/docs" if settings.exposes_api_docs() else None,
	redoc_url="/redoc" if settings.exposes_api_docs() else None,
	openapi_url="/openapi.json" if settings.exposes_api_docs() else None,
)
configure_logger()
register_exception_handlers(app)
app.include_router(health_router)
app.include_router(todos_router)
app.include_router(users_router)
app.include_router(auth_router)

if __name__ == "__main__":
	uvicorn.run("todos_app.main:app", host="0.0.0.0", port=8000, reload=True)
