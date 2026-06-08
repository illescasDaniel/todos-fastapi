from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from todos_app.core.settings import Settings, get_settings
from todos_app.domain.auth.access_token_issuer import AccessTokenIssuer
from todos_app.domain.auth.access_token_verifier import AccessTokenVerifier
from todos_app.domain.auth.password_hasher import PasswordHasher
from todos_app.domain.auth.user_auth_cache import UserAuthCache
from todos_app.domain.todos.repository import TodoRepository
from todos_app.domain.users.repository import UserRepository
from todos_app.infrastructure.auth.argon2_password_hasher import Argon2PasswordHasher
from todos_app.infrastructure.auth.jwt_access_token_issuer import JwtAccessTokenIssuer
from todos_app.infrastructure.auth.jwt_access_token_verifier import JwtAccessTokenVerifier
from todos_app.infrastructure.cache.valkey_client import create_valkey_client
from todos_app.infrastructure.cache.valkey_user_auth_cache import ValkeyUserAuthCache
from todos_app.infrastructure.persistence.database import get_db
from todos_app.infrastructure.persistence.todos.repository import SqlAlchemyTodoRepository
from todos_app.infrastructure.persistence.users.repository import SqlAlchemyUserRepository


DbSessionDep = Annotated[AsyncSession, Depends(get_db)]


def get_todo_repository(db: DbSessionDep) -> TodoRepository:
	return SqlAlchemyTodoRepository(db)


TodoRepositoryDep = Annotated[TodoRepository, Depends(get_todo_repository)]


def get_user_repository(db: DbSessionDep) -> UserRepository:
	return SqlAlchemyUserRepository(db)


UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]


def get_password_hasher() -> PasswordHasher:
	return Argon2PasswordHasher()


PasswordHasherDep = Annotated[PasswordHasher, Depends(get_password_hasher)]


def get_settings_dep() -> Settings:
	return get_settings()


SettingsDep = Annotated[Settings, Depends(get_settings_dep)]


def get_access_token_issuer(settings: SettingsDep) -> AccessTokenIssuer:
	return JwtAccessTokenIssuer(settings)


AccessTokenIssuerDep = Annotated[AccessTokenIssuer, Depends(get_access_token_issuer)]


def get_access_token_verifier(settings: SettingsDep) -> AccessTokenVerifier:
	return JwtAccessTokenVerifier(settings)


AccessTokenVerifierDep = Annotated[AccessTokenVerifier, Depends(get_access_token_verifier)]


def get_user_auth_cache(settings: SettingsDep) -> UserAuthCache:
	return ValkeyUserAuthCache(create_valkey_client(settings.valkey_url))


UserAuthCacheDep = Annotated[UserAuthCache, Depends(get_user_auth_cache)]
