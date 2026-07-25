import base64
import json

from todos_app.idempotency.domain.record import IdempotencyRecord


def serialize_idempotency_record(record: IdempotencyRecord) -> str:
	payload: dict[str, object] = {
		"state": record.state,
		"fingerprint": record.fingerprint,
	}
	if record.state == "completed":
		payload["status_code"] = record.status_code
		payload["body"] = base64.b64encode(record.body or b"").decode("ascii")
		payload["content_type"] = record.content_type or "application/json"
	return json.dumps(payload)


def deserialize_idempotency_record(payload: str) -> IdempotencyRecord | None:
	try:
		data = json.loads(payload)
	except json.JSONDecodeError:
		return None
	state = data.get("state")
	fingerprint = data.get("fingerprint")
	if state not in ("in_progress", "completed") or not isinstance(fingerprint, str):
		return None
	if state == "in_progress":
		return IdempotencyRecord(state="in_progress", fingerprint=fingerprint)
	status_code = data.get("status_code")
	body_raw = data.get("body")
	content_type = data.get("content_type")
	if not isinstance(status_code, int) or not isinstance(body_raw, str):
		return None
	try:
		body = base64.b64decode(body_raw.encode("ascii"))
	except ValueError:
		return None
	if not isinstance(content_type, str):
		content_type = "application/json"
	return IdempotencyRecord(
		state="completed",
		fingerprint=fingerprint,
		status_code=status_code,
		body=body,
		content_type=content_type,
	)
