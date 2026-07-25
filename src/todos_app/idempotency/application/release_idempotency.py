from todos_app.idempotency.domain.store import IdempotencyStore


async def release_idempotency(store: IdempotencyStore, *, scope_key: str) -> None:
	await store.release(scope_key)
