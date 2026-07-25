from collections.abc import AsyncIterable, Awaitable, Callable
from typing import cast
from uuid import UUID

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.datastructures import Headers
from starlette.responses import Response, StreamingResponse
from starlette.types import Message

from todos_app.auth.adapters.security.jwt_access_token_verifier import JwtAccessTokenVerifier
from todos_app.idempotency.adapters.api.factory import create_idempotency_store
from todos_app.idempotency.adapters.api.helpers import (
	build_scope_key,
	compute_request_fingerprint,
	is_idempotent_method,
	is_idempotent_path,
	read_idempotency_key,
)
from todos_app.idempotency.application.begin_idempotency import begin_idempotency
from todos_app.idempotency.application.complete_idempotency import complete_idempotency
from todos_app.idempotency.application.errors import IdempotencyKeyMismatchError, IdempotencyRequestInProgressError
from todos_app.idempotency.application.models import IdempotencyReplay
from todos_app.idempotency.application.release_idempotency import release_idempotency
from todos_app.shared.http_errors import (
	IDEMPOTENCY_KEY_INVALID,
	IDEMPOTENCY_KEY_MISMATCH,
	IDEMPOTENCY_REQUEST_IN_PROGRESS,
)
from todos_app.shared.settings import get_settings


def _extract_bearer_user_id(request: Request) -> UUID | None:
	auth_header = request.headers.get("authorization")
	if auth_header is None:
		return None
	parts = auth_header.split(" ", 1)
	if len(parts) != 2 or parts[0].lower() != "bearer":
		return None
	settings = get_settings()
	decoded = JwtAccessTokenVerifier(settings).decode(parts[1])
	if decoded is None:
		return None
	return decoded.user_id


def _replay_response(replay: IdempotencyReplay) -> Response:
	return Response(
		content=replay.body,
		status_code=replay.status_code,
		media_type=replay.content_type,
	)


def _error_response(status_code: int, detail: str) -> JSONResponse:
	return JSONResponse(status_code=status_code, content={"detail": detail})


async def _read_response_body(response: Response) -> tuple[bytes, Response]:
	body_chunks: list[bytes] = []
	body_iterator = cast(AsyncIterable[bytes], cast(StreamingResponse, response).body_iterator)
	async for chunk in body_iterator:
		body_chunks.append(chunk)
	body = b"".join(body_chunks)
	replayed = Response(
		content=body,
		status_code=response.status_code,
		headers=dict(response.headers),
		media_type=response.media_type,
	)
	return body, replayed


def _inject_body(request: Request, body: bytes) -> None:
	received = False

	async def receive() -> Message:
		nonlocal received
		if received:
			return {"type": "http.request", "body": b"", "more_body": False}
		received = True
		return {"type": "http.request", "body": body, "more_body": False}

	request.scope["receive"] = receive  # pyright: ignore[reportGeneralTypeIssues]


async def idempotency_middleware(
	request: Request,
	call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
	settings = get_settings()
	if not settings.idempotency.enabled:
		return await call_next(request)
	if not is_idempotent_method(request.method) or not is_idempotent_path(request.url.path):
		return await call_next(request)

	idempotency_key = read_idempotency_key(
		Headers(request.headers),
		max_key_length=settings.idempotency.max_key_length,
	)
	if idempotency_key is None:
		if request.headers.get("idempotency-key") is not None or request.headers.get("Idempotency-Key") is not None:
			return _error_response(status.HTTP_422_UNPROCESSABLE_ENTITY, IDEMPOTENCY_KEY_INVALID)
		return await call_next(request)

	body = await request.body()
	_inject_body(request, body)

	fingerprint = compute_request_fingerprint(
		method=request.method,
		path=request.url.path,
		query=request.url.query,
		body=body,
	)
	user_id = _extract_bearer_user_id(request)
	scope_key = build_scope_key(user_id=user_id, idempotency_key=idempotency_key)
	store = create_idempotency_store(settings)

	try:
		begin = await begin_idempotency(
			store,
			scope_key=scope_key,
			fingerprint=fingerprint,
			ttl_seconds=settings.idempotency.ttl_seconds,
		)
	except IdempotencyKeyMismatchError:
		return _error_response(status.HTTP_422_UNPROCESSABLE_ENTITY, IDEMPOTENCY_KEY_MISMATCH)
	except IdempotencyRequestInProgressError:
		return _error_response(status.HTTP_409_CONFLICT, IDEMPOTENCY_REQUEST_IN_PROGRESS)

	if begin.kind == "replay" and begin.replay is not None:
		return _replay_response(begin.replay)

	try:
		response = await call_next(request)
		response_body, replayed_response = await _read_response_body(response)
		content_type = response.media_type or response.headers.get("content-type") or "application/json"
		await complete_idempotency(
			store,
			scope_key=scope_key,
			fingerprint=fingerprint,
			status_code=response.status_code,
			body=response_body,
			content_type=content_type,
			ttl_seconds=settings.idempotency.ttl_seconds,
		)
		return replayed_response
	except Exception:
		await release_idempotency(store, scope_key=scope_key)
		raise
