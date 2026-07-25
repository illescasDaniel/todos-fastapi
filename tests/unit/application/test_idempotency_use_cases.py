import pytest

from fakes.idempotency_store import FakeIdempotencyStore
from todos_app.idempotency.application import idempotency as idempotency_use_cases
from todos_app.idempotency.application.errors import IdempotencyKeyMismatchError, IdempotencyRequestInProgressError
from todos_app.idempotency.domain.record import IdempotencyRecord


pytestmark = pytest.mark.unit


async def test_given_new_key_when_beginning_idempotency_then_proceeds() -> None:
	store = FakeIdempotencyStore()

	result = await idempotency_use_cases.begin_idempotency(
		store,
		scope_key="scope-1",
		fingerprint="fp-1",
		ttl_seconds=60,
	)

	assert result.kind == "proceed"
	assert result.replay is None


async def test_given_completed_record_when_beginning_with_same_fingerprint_then_replays() -> None:
	store = FakeIdempotencyStore()
	await store.complete(
		"scope-1",
		fingerprint="fp-1",
		status_code=201,
		body=b'{"id":"1"}',
		content_type="application/json",
		ttl_seconds=60,
	)

	result = await idempotency_use_cases.begin_idempotency(
		store,
		scope_key="scope-1",
		fingerprint="fp-1",
		ttl_seconds=60,
	)

	assert result.kind == "replay"
	assert result.replay is not None
	assert result.replay.status_code == 201
	assert result.replay.body == b'{"id":"1"}'


async def test_given_completed_record_when_beginning_with_different_fingerprint_then_raises_mismatch() -> None:
	store = FakeIdempotencyStore()
	await store.complete(
		"scope-1",
		fingerprint="fp-1",
		status_code=201,
		body=b"{}",
		content_type="application/json",
		ttl_seconds=60,
	)

	with pytest.raises(IdempotencyKeyMismatchError):
		await idempotency_use_cases.begin_idempotency(
			store,
			scope_key="scope-1",
			fingerprint="fp-2",
			ttl_seconds=60,
		)


async def test_given_in_progress_record_when_beginning_then_raises_in_progress() -> None:
	store = FakeIdempotencyStore()
	store.seed_in_progress("scope-1", fingerprint="fp-1")

	with pytest.raises(IdempotencyRequestInProgressError):
		await idempotency_use_cases.begin_idempotency(
			store,
			scope_key="scope-1",
			fingerprint="fp-1",
			ttl_seconds=60,
		)


async def test_given_acquire_race_when_beginning_then_raises_in_progress() -> None:
	store = FakeIdempotencyStore()
	store._records["scope-1"] = IdempotencyRecord(state="in_progress", fingerprint="fp-1")  # pyright: ignore[reportPrivateUsage]

	with pytest.raises(IdempotencyRequestInProgressError):
		await idempotency_use_cases.begin_idempotency(
			store,
			scope_key="scope-1",
			fingerprint="fp-1",
			ttl_seconds=60,
		)
