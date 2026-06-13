import json
from pathlib import Path

import pytest

from todos_mcp.config import Settings
from todos_mcp.scripts_runner import _resolve_script, open_api_docs, run_script


@pytest.fixture
def repo_root(tmp_path: Path) -> Path:
	scripts = tmp_path / "scripts"
	scripts.mkdir()
	(scripts / "echo.sh").write_text("#!/usr/bin/env bash\necho hello\n", encoding="utf-8")
	(scripts / "echo.sh").chmod(0o755)
	return tmp_path


@pytest.fixture
def settings(repo_root: Path) -> Settings:
	return Settings(api_base_url="http://127.0.0.1:8000", repo_root=repo_root)


def test_resolve_script_within_repo(settings: Settings) -> None:
	path = _resolve_script(settings, "scripts/echo.sh")
	assert path.name == "echo.sh"


def test_resolve_script_rejects_traversal(settings: Settings) -> None:
	with pytest.raises(ValueError, match="escapes repo root"):
		_resolve_script(settings, "../outside.sh")


def test_resolve_script_missing_file(settings: Settings) -> None:
	with pytest.raises(FileNotFoundError):
		_resolve_script(settings, "scripts/missing.sh")


def test_run_script(settings: Settings) -> None:
	result = run_script(settings, "scripts/echo.sh")
	payload = json.loads(result.to_json())
	assert payload["ok"] is True
	assert "hello" in payload["stdout"]


def test_open_api_docs_success(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
	opened: list[str] = []

	def fake_open(url: str, *_args: object, **_kwargs: object) -> bool:
		opened.append(url)
		return True

	monkeypatch.setattr("todos_mcp.scripts_runner.webbrowser.open", fake_open)
	result = open_api_docs(settings)
	payload = json.loads(result.to_json())
	assert payload["ok"] is True
	assert opened == ["http://127.0.0.1:8000/docs"]
	assert payload["url"] == "http://127.0.0.1:8000/docs"


def test_open_api_docs_failure(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
	monkeypatch.setattr("todos_mcp.scripts_runner.webbrowser.open", lambda *_a, **_k: False)
	result = open_api_docs(settings)
	payload = json.loads(result.to_json())
	assert payload["ok"] is False
	assert "Could not open browser" in payload["stderr"]
