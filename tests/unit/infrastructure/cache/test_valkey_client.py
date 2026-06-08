import pytest

from todos_app.infrastructure.cache.valkey_client import require_valkey_driver


pytestmark = pytest.mark.unit


def test_require_valkey_driver_raises_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
	def fake_import(name: str) -> object:
		if name == "valkey":
			raise ImportError("no valkey")
		return __import__(name)

	monkeypatch.setattr("importlib.import_module", fake_import)
	with pytest.raises(RuntimeError, match="pip install -e"):
		require_valkey_driver()
