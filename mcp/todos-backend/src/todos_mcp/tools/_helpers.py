import json

from todos_mcp import session


def resolve_access_token(access_token: str | None) -> str | None:
	"""Resolve the access token from the explicit argument or the session store.

	Security note: when `access_token` is passed explicitly it appears in tool
	call arguments and may be recorded in agent logs. Prefer calling `auth_login`
	once so the token is stored in the session and not repeated in subsequent calls.
	"""
	if access_token:
		return access_token
	return session.get_token()


def missing_token_response() -> str:
	return json.dumps(
		{
			"ok": False,
			"status": 401,
			"detail": "No access token. Call auth_login first or pass access_token.",
		},
		indent=2,
	)
