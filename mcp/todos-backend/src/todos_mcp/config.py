import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv


def _default_repo_root() -> Path:
	# .../todo/mcp/todos-backend/src/todos_mcp/config.py -> parents[4] == repo root
	return Path(__file__).resolve().parents[4]


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


def _default_api_base_url() -> str:
	try:
		host = os.environ["API_HOST"]
		port = os.environ["API_PORT"]
	except KeyError as exc:
		msg = f"Missing {exc.args[0]} — set it in config/ports.env or TODOS_API_BASE_URL"
		raise ValueError(msg) from exc
	return f"http://{host}:{port}"


_LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}


def _validate_api_base_url(url: str) -> str:
	"""Validate TODOS_API_BASE_URL to prevent SSRF attacks.

	Restricts target to loopback addresses unless MCP_ALLOW_REMOTE_API=true.
	"""
	parsed = urlparse(url)
	if parsed.scheme not in ("http", "https"):
		raise ValueError(f"TODOS_API_BASE_URL must use http or https scheme, got: {parsed.scheme!r}")
	host = parsed.hostname or ""
	allow_remote = os.getenv("MCP_ALLOW_REMOTE_API", "").lower() in ("1", "true", "yes")
	if host not in _LOOPBACK_HOSTS and not allow_remote:
		raise ValueError(
			f"TODOS_API_BASE_URL host {host!r} is not a loopback address. "
			"Set MCP_ALLOW_REMOTE_API=true to allow remote API targets."
		)
	return url


def _load_dotenv_file(env_path: Path) -> None:
	load_dotenv(env_path, override=False)


def _load_repo_env_files(repo_root: Path) -> None:
	for relative in ("config/ports.env", "config/ports.local.env", ".env"):
		_load_dotenv_file(repo_root / relative)


def load_settings() -> Settings:
	repo_root_raw = os.environ.get("TODOS_REPO_ROOT")
	repo_root = Path(repo_root_raw).resolve() if repo_root_raw else _default_repo_root()
	_load_repo_env_files(repo_root)
	api_base_url = _validate_api_base_url(os.environ.get("TODOS_API_BASE_URL", _default_api_base_url()).rstrip("/"))
	return Settings(api_base_url=api_base_url, repo_root=repo_root)
