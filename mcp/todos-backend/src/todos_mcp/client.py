import json
from typing import Any

import httpx

from todos_mcp.config import Settings


def _format_body(data: Any) -> Any:
	if data is None or data == "":
		return None
	return data


def _error_payload(status: int, detail: Any) -> dict[str, Any]:
	return {"ok": False, "status": status, "detail": detail}


def _success_payload(data: Any, status: int) -> dict[str, Any]:
	return {"ok": True, "status": status, "data": data}


class ApiClient:
	def __init__(self, settings: Settings) -> None:
		self._settings = settings

	async def request(
		self,
		method: str,
		path: str,
		*,
		json_body: dict[str, Any] | None = None,
		params: dict[str, Any] | None = None,
		access_token: str | None = None,
	) -> str:
		url = f"{self._settings.api_base_url}{path}"
		headers: dict[str, str] = {}
		if access_token is not None:
			headers["Authorization"] = f"Bearer {access_token}"

		try:
			async with httpx.AsyncClient(timeout=30.0) as client:
				response = await client.request(
					method,
					url,
					json=json_body,
					params=params,
					headers=headers,
				)
		except httpx.RequestError as exc:
			return json.dumps(
				_error_payload(0, f"Request failed: {exc}"),
				indent=2,
			)

		if response.status_code == 204:
			return json.dumps(_success_payload(None, 204), indent=2)

		try:
			body = response.json()
		except json.JSONDecodeError:
			body = _format_body(response.text)

		if response.is_success:
			return json.dumps(_success_payload(body, response.status_code), indent=2)

		detail = body.get("detail", body) if isinstance(body, dict) else body
		return json.dumps(_error_payload(response.status_code, detail), indent=2)
