from todos_app.domain.idempotency.record import IdempotencyRecord


class FakeIdempotencyStore:
	def __init__(self) -> None:
		self._records: dict[str, IdempotencyRecord] = {}

	def clear(self) -> None:
		self._records.clear()

	def seed_in_progress(self, scope_key: str, *, fingerprint: str) -> None:
		self._records[scope_key] = IdempotencyRecord(state="in_progress", fingerprint=fingerprint)

	async def get(self, scope_key: str) -> IdempotencyRecord | None:
		return self._records.get(scope_key)

	async def try_acquire(self, scope_key: str, *, fingerprint: str, ttl_seconds: int) -> bool:
		if scope_key in self._records:
			return False
		self._records[scope_key] = IdempotencyRecord(state="in_progress", fingerprint=fingerprint)
		return True

	async def complete(
		self,
		scope_key: str,
		*,
		fingerprint: str,
		status_code: int,
		body: bytes,
		content_type: str,
		ttl_seconds: int,
	) -> None:
		self._records[scope_key] = IdempotencyRecord(
			state="completed",
			fingerprint=fingerprint,
			status_code=status_code,
			body=body,
			content_type=content_type,
		)

	async def release(self, scope_key: str) -> None:
		self._records.pop(scope_key, None)
