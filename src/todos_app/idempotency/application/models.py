from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class IdempotencyReplay:
	status_code: int
	body: bytes
	content_type: str


@dataclass(frozen=True, slots=True)
class IdempotencyBeginResult:
	kind: Literal["proceed", "replay"]
	replay: IdempotencyReplay | None = None
