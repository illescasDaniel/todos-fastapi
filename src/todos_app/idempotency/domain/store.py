from typing import Protocol

from todos_app.idempotency.domain.record import IdempotencyRecord


class IdempotencyStore(Protocol):
	async def get(self, scope_key: str) -> IdempotencyRecord | None: ...

	async def try_acquire(self, scope_key: str, *, fingerprint: str, ttl_seconds: int) -> bool: ...

	async def complete(
		self,
		scope_key: str,
		*,
		fingerprint: str,
		status_code: int,
		body: bytes,
		content_type: str,
		ttl_seconds: int,
	) -> None: ...

	async def release(self, scope_key: str) -> None: ...
