import hashlib
from collections.abc import Mapping
from urllib.parse import parse_qsl, urlencode
from uuid import UUID


_IDEMPOTENCY_HEADER = "idempotency-key"
_EXCLUDED_PATHS = frozenset({"/auth/login"})


def idempotency_header_name() -> str:
	return "Idempotency-Key"


def is_idempotent_method(method: str) -> bool:
	return method.upper() in {"POST", "PUT", "PATCH", "DELETE"}


def is_idempotent_path(path: str) -> bool:
	if path.startswith("/health"):
		return False
	return path not in _EXCLUDED_PATHS


def normalize_query_string(query: str) -> str:
	if not query:
		return ""
	return urlencode(sorted(parse_qsl(query)))


def compute_request_fingerprint(
	*,
	method: str,
	path: str,
	query: str,
	body: bytes,
) -> str:
	normalized_query = normalize_query_string(query)
	payload = "\n".join(
		[
			method.upper(),
			path,
			normalized_query,
			body.decode("latin-1"),
		]
	)
	return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_scope_key(*, user_id: UUID | None, idempotency_key: str) -> str:
	if user_id is not None:
		return f"idempotency:{user_id}:{idempotency_key}"
	return f"idempotency:anon:{idempotency_key}"


def read_idempotency_key(headers: Mapping[str, str], *, max_key_length: int) -> str | None:
	raw = headers.get(_IDEMPOTENCY_HEADER) or headers.get("Idempotency-Key")
	if raw is None:
		return None
	key = raw.strip()
	if not key or len(key) > max_key_length:
		return None
	return key
