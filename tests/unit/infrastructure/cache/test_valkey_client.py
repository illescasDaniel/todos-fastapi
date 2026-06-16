import pytest

from todos_app.infrastructure.cache.valkey_client import require_valkey_driver


pytestmark = pytest.mark.unit


def test_given_missing_valkey_module_when_requiring_driver_then_raises_runtime_error(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	# given
	def fake_import(name: str) -> object:
		if name == "valkey":
			raise ImportError("no valkey")
		return __import__(name)

	monkeypatch.setattr("importlib.import_module", fake_import)

	# when
	with pytest.raises(RuntimeError, match="pip install -e"):
		require_valkey_driver()

	# then
