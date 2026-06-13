from mcp.server.fastmcp import FastMCP

from todos_mcp.client import ApiClient
from todos_mcp.config import Settings


def register(mcp: FastMCP, settings: Settings, client: ApiClient) -> None:
	@mcp.tool()
	async def health_check() -> str:
		"""Check API liveness (GET /health). Returns {"status": "ok"} when the server is up."""
		return await client.request("GET", "/health")
