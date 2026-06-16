import os
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


_LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}


def _ensure_src_importable(repo_root: Path) -> None:
	src = str((repo_root / "src").resolve())
	if src not in sys.path:
		sys.path.insert(0, src)


@dataclass(frozen=True, slots=True)
class Settings:
	api_base_url: str
	repo_root: Path

	@property
	def health_url(self) -> str:
		return f"{self.api_base_url}/health"

	@property
	def docs_url(self) -> str:
		return f"{self.api_base_url}/docs"


def _validate_api_base_url(url: str, *, allow_remote: bool) -> str:
	parsed = urlparse(url)
	if parsed.scheme not in ("http", "https"):
		raise ValueError(f"MCP_API_BASE_URL must use http or https scheme, got: {parsed.scheme!r}")
	host = parsed.hostname or ""
	if host not in _LOOPBACK_HOSTS and not allow_remote:
		raise ValueError(
			f"MCP_API_BASE_URL host {host!r} is not a loopback address. "
			"Set mcp_allow_remote_api=true in the env profile to allow remote API targets."
		)
	return url


def load_settings() -> Settings:
	if not os.environ.get("ENV_PROFILE"):
		raise RuntimeError(
			"ENV_PROFILE must be set to a profile module name (e.g. local, test). "
			"Configure it in .cursor/mcp.json or export before starting the MCP server."
		)
	repo_root_raw = os.environ.get("TODOS_REPO_ROOT")
	if not repo_root_raw:
		raise RuntimeError(
			"TODOS_REPO_ROOT must be set to the repository root path. "
			"Add TODOS_REPO_ROOT to .cursor/mcp.json env (e.g. ${workspaceFolder})."
		)
	repo_root = Path(repo_root_raw).resolve()
	_ensure_src_importable(repo_root)

	from todos_app.core.config.loader import get_env_settings

	app_settings = get_env_settings()
	api_base_url = _validate_api_base_url(
		app_settings.mcp.api_base_url.rstrip("/"),
		allow_remote=app_settings.mcp.allow_remote_api,
	)
	return Settings(api_base_url=api_base_url, repo_root=repo_root)
