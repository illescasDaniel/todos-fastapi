import os
from dataclasses import dataclass
from pathlib import Path


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


def _default_api_base_url() -> str:
    host = os.environ.get("API_HOST", "127.0.0.1")
    port = os.environ.get("API_PORT", "8000")
    return f"http://{host}:{port}"


def load_settings() -> Settings:
    api_base_url = os.environ.get("TODOS_API_BASE_URL", _default_api_base_url()).rstrip("/")
    repo_root_raw = os.environ.get("TODOS_REPO_ROOT")
    repo_root = Path(repo_root_raw).resolve() if repo_root_raw else _default_repo_root()
    return Settings(api_base_url=api_base_url, repo_root=repo_root)
