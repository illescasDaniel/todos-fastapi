from todos_mcp import session


def test_session_roundtrip() -> None:
    session.clear_token()
    assert session.get_token() is None
    session.set_token("abc")
    assert session.get_token() == "abc"
    session.clear_token()
    assert session.get_token() is None
