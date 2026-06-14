import atexit

from todos_mcp import session
from todos_mcp.server import create_mcp


def main() -> None:
	atexit.register(session.clear_token)
	mcp = create_mcp()
	mcp.run()


if __name__ == "__main__":
	main()
