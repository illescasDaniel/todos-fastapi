from typing import Annotated

from fastapi import Depends

from todos_app.auth.adapters.cache.valkey_user_auth_cache import ValkeyUserAuthCache
from todos_app.auth.adapters.security.argon2_password_hasher import Argon2PasswordHasher
from todos_app.auth.adapters.security.jwt_access_token_issuer import JwtAccessTokenIssuer
from todos_app.auth.adapters.security.jwt_access_token_verifier import JwtAccessTokenVerifier
from todos_app.auth.domain.access_token_issuer import AccessTokenIssuer
from todos_app.auth.domain.access_token_verifier import AccessTokenVerifier
from todos_app.auth.domain.password_hasher import PasswordHasher
from todos_app.auth.domain.user_auth_cache import UserAuthCache
from todos_app.auth.domain.user_lookup import UserLookup
from todos_app.shared.adapters.cache.valkey_client import create_valkey_client
from todos_app.shared.dependencies import SettingsDep
from todos_app.users.adapters.api.dependencies import UserRepositoryDep
from todos_app.users.adapters.database.user_lookup import UserRepositoryLookup


def get_password_hasher(settings: SettingsDep) -> PasswordHasher:
	return Argon2PasswordHasher(settings)


PasswordHasherDep = Annotated[PasswordHasher, Depends(get_password_hasher)]


def get_access_token_issuer(settings: SettingsDep) -> AccessTokenIssuer:
	return JwtAccessTokenIssuer(settings)


AccessTokenIssuerDep = Annotated[AccessTokenIssuer, Depends(get_access_token_issuer)]


def get_access_token_verifier(settings: SettingsDep) -> AccessTokenVerifier:
	return JwtAccessTokenVerifier(settings)


AccessTokenVerifierDep = Annotated[AccessTokenVerifier, Depends(get_access_token_verifier)]


def get_user_auth_cache(settings: SettingsDep) -> UserAuthCache:
	return ValkeyUserAuthCache(create_valkey_client(settings.valkey.url))


UserAuthCacheDep = Annotated[UserAuthCache, Depends(get_user_auth_cache)]


def get_user_lookup(repo: UserRepositoryDep) -> UserLookup:
	return UserRepositoryLookup(repo)


UserLookupDep = Annotated[UserLookup, Depends(get_user_lookup)]
