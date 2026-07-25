from unittest.mock import AsyncMock

import pytest

from todos_app.idempotency.adapters.cache.idempotency_codec import serialize_idempotency_record
from todos_app.idempotency.adapters.cache.valkey_idempotency_store import ValkeyIdempotencyStore
from todos_app.idempotency.domain.record import IdempotencyRecord


pytestmark = pytest.mark.unit


@pytest.fixture
def valkey_client() -> AsyncMock:
	return AsyncMock()


@pytest.fixture
def store(valkey_client: AsyncMock) -> ValkeyIdempotencyStore:
	return ValkeyIdempotencyStore(valkey_client)


async def test_given_missing_key_when_getting_then_returns_none(
	store: ValkeyIdempotencyStore, valkey_client: AsyncMock
) -> None:
	valkey_client.get.return_value = None

	result = await store.get("scope-1")

	assert result is None


async def test_given_acquire_success_when_trying_acquire_then_returns_true(
	store: ValkeyIdempotencyStore,
	valkey_client: AsyncMock,
) -> None:
	valkey_client.set.return_value = True

	acquired = await store.try_acquire("scope-1", fingerprint="fp-1", ttl_seconds=60)

	assert acquired is True
	valkey_client.set.assert_awaited_once()
	kwargs = valkey_client.set.await_args.kwargs
	assert kwargs["nx"] is True
	assert kwargs["ex"] == 60


async def test_given_completed_record_when_completing_then_overwrites_key(
	store: ValkeyIdempotencyStore,
	valkey_client: AsyncMock,
) -> None:
	await store.complete(
		"scope-1",
		fingerprint="fp-1",
		status_code=201,
		body=b'{"ok":true}',
		content_type="application/json",
		ttl_seconds=120,
	)

	valkey_client.set.assert_awaited_once()
	args = valkey_client.set.await_args.args
	assert args[0] == "scope-1"
	record = serialize_idempotency_record(
		IdempotencyRecord(
			state="completed",
			fingerprint="fp-1",
			status_code=201,
			body=b'{"ok":true}',
			content_type="application/json",
		)
	)
	assert args[1] == record
