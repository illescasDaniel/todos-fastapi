import pytest

from todos_app.core.idempotency import (
	build_scope_key,
	compute_request_fingerprint,
	is_idempotent_method,
	is_idempotent_path,
	normalize_query_string,
	read_idempotency_key,
)
from todos_app.domain.ids import JANE_USER_ID


pytestmark = pytest.mark.unit


def test_given_mutating_methods_when_checking_idempotency_then_only_writes_match() -> None:
	assert is_idempotent_method("POST")
	assert is_idempotent_method("delete")
	assert not is_idempotent_method("GET")


def test_given_health_and_login_paths_when_checking_idempotency_then_excluded() -> None:
	assert not is_idempotent_path("/health")
	assert not is_idempotent_path("/auth/login")
	assert is_idempotent_path("/todos")


def test_given_unsorted_query_when_normalizing_then_sorts_pairs() -> None:
	assert normalize_query_string("b=2&a=1") == "a=1&b=2"


def test_given_same_request_parts_when_computing_fingerprint_then_stable() -> None:
	first = compute_request_fingerprint(method="POST", path="/todos", query="", body=b'{"title":"x"}')
	second = compute_request_fingerprint(method="POST", path="/todos", query="", body=b'{"title":"x"}')
	third = compute_request_fingerprint(method="POST", path="/todos", query="", body=b'{"title":"y"}')

	assert first == second
	assert first != third


def test_given_authenticated_user_when_building_scope_key_then_includes_user_id() -> None:
	assert build_scope_key(user_id=JANE_USER_ID, idempotency_key="key-1") == f"idempotency:{JANE_USER_ID}:key-1"


def test_given_anonymous_request_when_building_scope_key_then_uses_anon_prefix() -> None:
	assert build_scope_key(user_id=None, idempotency_key="key-1") == "idempotency:anon:key-1"


def test_given_blank_idempotency_header_when_reading_then_returns_none() -> None:
	assert read_idempotency_key({"Idempotency-Key": "   "}, max_key_length=255) is None


def test_given_valid_idempotency_header_when_reading_then_returns_trimmed_key() -> None:
	assert read_idempotency_key({"Idempotency-Key": "  abc  "}, max_key_length=255) == "abc"
