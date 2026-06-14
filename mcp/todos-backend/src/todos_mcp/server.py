from mcp.server.fastmcp import FastMCP

from todos_mcp.client import ApiClient
from todos_mcp.config import Settings, load_settings
from todos_mcp.tools import auth, health, lifecycle, todos, users


def create_mcp(settings: Settings | None = None) -> FastMCP:
	resolved = settings or load_settings()
	mcp = FastMCP("todos-backend")
	client = ApiClient(resolved)

	health.register(mcp, resolved, client)
	auth.register(mcp, resolved, client)
	users.register(mcp, resolved, client)
	todos.register(mcp, resolved, client)
	lifecycle.register(mcp, resolved)

	return mcp
