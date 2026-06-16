import pytest

from todos_mcp.config import load_settings


def test_load_settings_reads_test_profile(monkeypatch: pytest.MonkeyPatch) -> None:
	repo_root = __import__("pathlib").Path(__file__).resolve().parents[3]
	monkeypatch.setenv("ENV_PROFILE", "test")
	monkeypatch.setenv("TODOS_REPO_ROOT", str(repo_root))
	settings = load_settings()
	assert settings.api_base_url == "http://127.0.0.1:8000"
	assert settings.repo_root == repo_root
