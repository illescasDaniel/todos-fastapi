import importlib
from typing import TYPE_CHECKING


if TYPE_CHECKING:
	from valkey.asyncio import Valkey


def require_valkey_driver() -> None:
	try:
		importlib.import_module("valkey")
	except ImportError as exc:
		message = 'Valkey driver "valkey" is not installed. Reinstall the project: pip install -e ".[dev]"'
		raise RuntimeError(message) from exc


def create_valkey_client(valkey_url: str) -> Valkey:
	require_valkey_driver()
	from valkey.asyncio import Valkey

	return Valkey.from_url(valkey_url, decode_responses=True)
