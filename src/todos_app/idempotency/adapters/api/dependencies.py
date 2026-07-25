from typing import Annotated

from fastapi import Depends

from todos_app.idempotency.adapters.cache.valkey_idempotency_store import ValkeyIdempotencyStore
from todos_app.idempotency.domain.store import IdempotencyStore
from todos_app.shared.adapters.cache.valkey_client import create_valkey_client
from todos_app.shared.dependencies import SettingsDep


def get_idempotency_store(settings: SettingsDep) -> IdempotencyStore:
	return ValkeyIdempotencyStore(create_valkey_client(settings.valkey.url))


IdempotencyStoreDep = Annotated[IdempotencyStore, Depends(get_idempotency_store)]
