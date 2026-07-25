import uvicorn

from todos_app.runtime.app import create_app


app = create_app()

if __name__ == "__main__":
	uvicorn.run("todos_app.main:app", host="0.0.0.0", port=8000, reload=True)
