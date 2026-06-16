from dataclasses import dataclass
from typing import Any
from uuid import UUID

from httpx import AsyncClient

from factories import user_signup_payload
from fakes.fast_password_hasher import get_test_password_hasher
from todos_app.domain.users.entity import User
from todos_app.infrastructure.persistence.database import AsyncSessionLocal
from todos_app.infrastructure.persistence.users.repository import SqlAlchemyUserRepository


_TEST_PASSWORD_HASHER = get_test_password_hasher()


@dataclass(frozen=True)
class AuthenticatedTestUser:
	payload: dict[str, Any]
	user_id: UUID
	token: str


async def create_user_in_db(
	*,
	role: str = "user",
	is_active: bool = True,
	**overrides: Any,
) -> tuple[dict[str, Any], UUID]:
	signup_overrides = {key: value for key, value in overrides.items() if key not in {"role", "is_active"}}
	effective_role = str(overrides.get("role", role))
	effective_is_active = bool(overrides.get("is_active", is_active))
	payload = user_signup_payload(**signup_overrides)
	async with AsyncSessionLocal() as session:
		repo = SqlAlchemyUserRepository(session)
		created = await repo.add(
			User(
				id=None,
				email=payload["email"],
				username=payload["username"],
				first_name=payload["first_name"],
				last_name=payload["last_name"],
				hashed_password=_TEST_PASSWORD_HASHER.hash(payload["password"]),
				is_active=effective_is_active,
				role=effective_role,
			)
		)
		await session.commit()
		if created.id is None:
			raise RuntimeError("repository did not assign user id on insert")
		return payload, created.id


async def login_user(client: AsyncClient, payload: dict[str, Any]) -> str:
	login_response = await client.post(
		"/auth/login",
		json={"username": payload["username"], "password": payload["password"]},
	)
	assert login_response.status_code == 200
	return login_response.json()["access_token"]


async def register_and_login(client: AsyncClient, **user_overrides: Any) -> AuthenticatedTestUser:
	payload, user_id = await create_user_in_db(**user_overrides)
	token = await login_user(client, payload)
	return AuthenticatedTestUser(payload=payload, user_id=user_id, token=token)


async def register_admin_and_login(client: AsyncClient, **user_overrides: Any) -> AuthenticatedTestUser:
	signup_overrides = {key: value for key, value in user_overrides.items() if key not in {"role", "is_active"}}
	is_active = bool(user_overrides.get("is_active", True))
	return await register_and_login(client, role="admin", is_active=is_active, **signup_overrides)


def auth_headers(token: str) -> dict[str, str]:
	return {"Authorization": f"Bearer {token}"}
