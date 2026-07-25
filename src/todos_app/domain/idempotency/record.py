from dataclasses import dataclass
from typing import Literal


IdempotencyState = Literal["in_progress", "completed"]


@dataclass(frozen=True, slots=True)
class IdempotencyRecord:
	state: IdempotencyState
	fingerprint: str
	status_code: int | None = None
	body: bytes | None = None
	content_type: str | None = None
