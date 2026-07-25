from dataclasses import dataclass
from typing import Literal

from todos_app.idempotency.application.errors import IdempotencyKeyMismatchError, IdempotencyRequestInProgressError
from todos_app.idempotency.domain.record import IdempotencyRecord
from todos_app.idempotency.domain.store import IdempotencyStore


@dataclass(frozen=True, slots=True)
class IdempotencyReplay:
	status_code: int
	body: bytes
	content_type: str


@dataclass(frozen=True, slots=True)
class IdempotencyBeginResult:
	kind: Literal["proceed", "replay"]
	replay: IdempotencyReplay | None = None


async def begin_idempotency(
	store: IdempotencyStore,
	*,
	scope_key: str,
	fingerprint: str,
	ttl_seconds: int,
) -> IdempotencyBeginResult:
	existing = await store.get(scope_key)
	if existing is None:
		acquired = await store.try_acquire(scope_key, fingerprint=fingerprint, ttl_seconds=ttl_seconds)
		if acquired:
			return IdempotencyBeginResult(kind="proceed")
		existing = await store.get(scope_key)
		if existing is None:
			raise IdempotencyRequestInProgressError

	return _resolve_existing(existing, fingerprint=fingerprint)


def _resolve_existing(existing: IdempotencyRecord, *, fingerprint: str) -> IdempotencyBeginResult:
	if existing.state == "in_progress":
		raise IdempotencyRequestInProgressError
	if existing.fingerprint != fingerprint:
		raise IdempotencyKeyMismatchError
	if existing.status_code is None or existing.body is None:
		raise IdempotencyRequestInProgressError
	return IdempotencyBeginResult(
		kind="replay",
		replay=IdempotencyReplay(
			status_code=existing.status_code,
			body=existing.body,
			content_type=existing.content_type or "application/json",
		),
	)


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


async def release_idempotency(store: IdempotencyStore, *, scope_key: str) -> None:
	await store.release(scope_key)
