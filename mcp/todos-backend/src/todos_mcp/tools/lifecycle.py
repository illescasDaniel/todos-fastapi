import json

from mcp.server.fastmcp import FastMCP

from todos_mcp.config import Settings
from todos_mcp.scripts_runner import (
    run_script,
    stack_health_curl,
    start_host_background,
    stop_host_background,
)


def register(mcp: FastMCP, settings: Settings) -> None:
    @mcp.tool()
    async def stack_health() -> str:
        """Check whether the API responds at TODOS_API_BASE_URL/health (curl)."""
        return stack_health_curl(settings).to_json()

    @mcp.tool()
    async def stack_start_host(mode: str = "dev") -> str:
        """Start the host API in background via ./scripts/start.sh (Path A).

        mode: 'dev' (hot reload) or 'pro'. Prefer stack_compose_up for daemonized stacks.
        Only one MCP-spawned host process is tracked at a time.
        """
        if mode not in ("dev", "pro"):
            return json.dumps(
                {"ok": False, "detail": "mode must be 'dev' or 'pro'"},
                indent=2,
            )
        return start_host_background(settings, mode=mode).to_json()

    @mcp.tool()
    async def stack_stop_host() -> str:
        """Stop the MCP-spawned host API process (SIGTERM to process group)."""
        return stop_host_background().to_json()

    @mcp.tool()
    async def stack_compose_up() -> str:
        """Start full local stack via ./scripts/container/up.sh (Path B). Waits for /health."""
        return run_script(settings, "scripts/container/up.sh", timeout=900).to_json()

    @mcp.tool()
    async def stack_compose_down(remove: bool = False) -> str:
        """Stop compose stack via ./scripts/container/down.sh. Set remove=true for compose down."""
        args = ("--remove",) if remove else ()
        return run_script(settings, "scripts/container/down.sh", *args).to_json()

    @mcp.tool()
    async def db_migrate() -> str:
        """Run Alembic upgrade via ./scripts/migrate.sh."""
        return run_script(settings, "scripts/migrate.sh").to_json()

    @mcp.tool()
    async def db_seed() -> str:
        """Seed demo data via ./scripts/seed.sh. Requires APP_ENV=local in repo .env."""
        return run_script(settings, "scripts/seed.sh").to_json()

    @mcp.tool()
    async def db_wipe() -> str:
        """DESTRUCTIVE: wipe local DB volumes via ./scripts/wipe.sh --yes."""
        return run_script(settings, "scripts/wipe.sh", "--yes", timeout=900).to_json()
