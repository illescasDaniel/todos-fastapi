_access_token: str | None = None


def get_token() -> str | None:
    return _access_token


def set_token(token: str) -> None:
    global _access_token
    _access_token = token


def clear_token() -> None:
    global _access_token
    _access_token = None
