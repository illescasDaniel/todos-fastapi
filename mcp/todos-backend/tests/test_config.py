import os
from pathlib import Path

import pytest

from todos_mcp.config import _load_repo_dotenv, load_settings


def test_load_repo_dotenv_sets_unset_keys(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
	monkeypatch.delenv("MCP_ALLOW_DESTRUCTIVE", raising=False)
	(tmp_path / ".env").write_text(
		"# comment\nMCP_ALLOW_DESTRUCTIVE=true\nAPI_PORT=9001\n",
		encoding="utf-8",
	)
	_load_repo_dotenv(tmp_path)
	assert os.environ["MCP_ALLOW_DESTRUCTIVE"] == "true"
	assert os.environ["API_PORT"] == "9001"


def test_load_repo_dotenv_does_not_override_existing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
	monkeypatch.setenv("MCP_ALLOW_DESTRUCTIVE", "false")
	(tmp_path / ".env").write_text("MCP_ALLOW_DESTRUCTIVE=true\n", encoding="utf-8")
	_load_repo_dotenv(tmp_path)
	assert os.environ["MCP_ALLOW_DESTRUCTIVE"] == "false"


def test_load_settings_reads_repo_dotenv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
	monkeypatch.delenv("TODOS_API_BASE_URL", raising=False)
	monkeypatch.delenv("API_PORT", raising=False)
	monkeypatch.setenv("TODOS_REPO_ROOT", str(tmp_path))
	(tmp_path / ".env").write_text("API_PORT=9001\n", encoding="utf-8")
	settings = load_settings()
	assert settings.api_base_url == "http://127.0.0.1:9001"
