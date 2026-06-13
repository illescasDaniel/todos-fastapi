from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from todos_app.core.dependencies import AccessTokenVerifierDep, SettingsDep, UserAuthCacheDep, UserRepositoryDep
from todos_app.core.http_errors import INVALID_TOKEN
from todos_app.domain.auth.authenticated_user import AuthenticatedUser


http_bearer = HTTPBearer(auto_error=False)


def _unauthorized() -> HTTPException:
	return HTTPException(
		status_code=status.HTTP_401_UNAUTHORIZED,
		detail=INVALID_TOKEN,
		headers={"WWW-Authenticate": "Bearer"},
	)


async def get_current_user(
	credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(http_bearer)],
	verifier: AccessTokenVerifierDep,
	repo: UserRepositoryDep,
	auth_cache: UserAuthCacheDep,
	settings: SettingsDep,
) -> AuthenticatedUser:
	if credentials is None or credentials.scheme.lower() != "bearer":
		raise _unauthorized()
	decoded = verifier.decode(credentials.credentials)
	if decoded is None:
		raise _unauthorized()
	# Always fetch from DB to get fresh role/is_active (M5) and verify token_version (H1).
	db_user = await repo.get_by_id(decoded.user_id)
	if db_user is None or db_user.id is None or not db_user.is_active:
		raise _unauthorized()
	if db_user.token_version != decoded.token_version:
		raise _unauthorized()
	auth_user = AuthenticatedUser(
		user_id=db_user.id,
		username=db_user.username,
		role=db_user.role,
	)
	await auth_cache.set_active_user(auth_user, ttl_seconds=settings.auth_user_cache_ttl_seconds)
	return auth_user


CurrentUserDep = Annotated[AuthenticatedUser, Depends(get_current_user)]
