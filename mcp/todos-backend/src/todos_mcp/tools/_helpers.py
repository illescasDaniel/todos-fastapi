import json

from todos_mcp import session


def resolve_access_token(access_token: str | None) -> str | None:
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
