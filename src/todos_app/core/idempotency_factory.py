from collections.abc import Callable

from todos_app.core.settings import Settings, get_settings
from todos_app.domain.idempotency.store import IdempotencyStore
from todos_app.infrastructure.cache.valkey_client import create_valkey_client
from todos_app.infrastructure.cache.valkey_idempotency_store import ValkeyIdempotencyStore


_idempotency_store_factory: Callable[[], IdempotencyStore] | None = None


def set_idempotency_store_factory(factory: Callable[[], IdempotencyStore] | None) -> None:
	global _idempotency_store_factory
	_idempotency_store_factory = factory


def create_idempotency_store(settings: Settings | None = None) -> IdempotencyStore:
	if _idempotency_store_factory is not None:
		return _idempotency_store_factory()
	resolved = settings or get_settings()
	return ValkeyIdempotencyStore(create_valkey_client(resolved.valkey.url))
