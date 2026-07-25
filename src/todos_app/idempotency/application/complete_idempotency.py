from todos_app.idempotency.domain.store import IdempotencyStore


async def complete_idempotency(
	store: IdempotencyStore,
	*,
	scope_key: str,
	fingerprint: str,
	status_code: int,
	body: bytes,
	content_type: str,
	ttl_seconds: int,
) -> None:
	await store.complete(
		scope_key,
		fingerprint=fingerprint,
		status_code=status_code,
		body=body,
		content_type=content_type,
		ttl_seconds=ttl_seconds,
	)
