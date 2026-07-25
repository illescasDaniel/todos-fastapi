import pytest

from todos_app.idempotency.adapters.cache.idempotency_codec import (
	deserialize_idempotency_record,
	serialize_idempotency_record,
)
from todos_app.idempotency.domain.record import IdempotencyRecord


pytestmark = pytest.mark.unit


def test_given_in_progress_record_when_round_tripping_codec_then_preserves_state() -> None:
	record = IdempotencyRecord(state="in_progress", fingerprint="abc123")

	payload = serialize_idempotency_record(record)
	restored = deserialize_idempotency_record(payload)

	assert restored == record


def test_given_completed_record_when_round_tripping_codec_then_preserves_response() -> None:
	record = IdempotencyRecord(
		state="completed",
		fingerprint="abc123",
		status_code=204,
		body=b"",
		content_type="application/json",
	)

	payload = serialize_idempotency_record(record)
	restored = deserialize_idempotency_record(payload)

	assert restored == record


def test_given_invalid_payload_when_deserializing_then_returns_none() -> None:
	assert deserialize_idempotency_record("not-json") is None
