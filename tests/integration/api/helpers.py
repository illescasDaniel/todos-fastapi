from typing import Any

from httpx import AsyncClient

from factories import user_signup_payload
from todos_app.domain.users.entity import User
from todos_app.infrastructure.auth.argon2_password_hasher import Argon2PasswordHasher
from todos_app.infrastructure.persistence.database import AsyncSessionLocal
from todos_app.infrastructure.persistence.users.repository import SqlAlchemyUserRepository


async def register_and_login(client: AsyncClient, **user_overrides: Any) -> tuple[dict[str, Any], str]:
	payload = user_signup_payload(**user_overrides)
	create_response = await client.post("/users", json=payload)
	assert create_response.status_code == 201

	login_response = await client.post(
		"/auth/login",
		json={"username": payload["username"], "password": payload["password"]},
	)
	assert login_response.status_code == 200
	token = login_response.json()["access_token"]
	return payload, token


async def register_admin_and_login(client: AsyncClient, **user_overrides: Any) -> tuple[dict[str, Any], str]:
	payload = user_signup_payload(**user_overrides)
	hasher = Argon2PasswordHasher()
	async with AsyncSessionLocal() as session:
		repo = SqlAlchemyUserRepository(session)
		await repo.add(
			User(
				id=None,
				email=payload["email"],
				username=payload["username"],
				first_name=payload["first_name"],
				last_name=payload["last_name"],
				hashed_password=hasher.hash(payload["password"]),
				is_active=True,
				role="admin",
			)
		)
		await session.commit()

	login_response = await client.post(
		"/auth/login",
		json={"username": payload["username"], "password": payload["password"]},
	)
	assert login_response.status_code == 200
	token = login_response.json()["access_token"]
	return payload, token


def auth_headers(token: str) -> dict[str, str]:
	return {"Authorization": f"Bearer {token}"}
