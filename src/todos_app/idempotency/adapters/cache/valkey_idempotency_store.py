from typing import TYPE_CHECKING

from todos_app.idempotency.adapters.cache.idempotency_codec import (
	deserialize_idempotency_record,
	serialize_idempotency_record,
)
from todos_app.idempotency.domain.record import IdempotencyRecord


if TYPE_CHECKING:
	from valkey.asyncio import Valkey


class ValkeyIdempotencyStore:
	def __init__(self, client: Valkey) -> None:
		self._client = client

	async def get(self, scope_key: str) -> IdempotencyRecord | None:
		payload = await self._client.get(scope_key)
		if payload is None:
			return None
		if not isinstance(payload, str):
			return None
		return deserialize_idempotency_record(payload)

	async def try_acquire(self, scope_key: str, *, fingerprint: str, ttl_seconds: int) -> bool:
		record = IdempotencyRecord(state="in_progress", fingerprint=fingerprint)
		result = await self._client.set(
			scope_key,
			serialize_idempotency_record(record),
			nx=True,
			ex=ttl_seconds,
		)
		return bool(result)

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
		record = IdempotencyRecord(
			state="completed",
			fingerprint=fingerprint,
			status_code=status_code,
			body=body,
			content_type=content_type,
		)
		await self._client.set(
			scope_key,
			serialize_idempotency_record(record),
			ex=ttl_seconds,
		)

	async def release(self, scope_key: str) -> None:
		await self._client.delete(scope_key)
