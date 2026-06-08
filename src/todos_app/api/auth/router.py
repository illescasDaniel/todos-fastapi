from fastapi import APIRouter

from todos_app.api.auth.schemas import LoginRequest, TokenResponse
from todos_app.api.openapi_responses import OpenAPIResponse
from todos_app.application import auth as auth_use_cases
from todos_app.core.dependencies import AccessTokenIssuerDep, PasswordHasherDep, UserRepositoryDep


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
	"/login",
	response_model=TokenResponse,
	responses=OpenAPIResponse.merge(OpenAPIResponse.INVALID_CREDENTIALS),
)
async def login(
	body: LoginRequest,
	repo: UserRepositoryDep,
	hasher: PasswordHasherDep,
	issuer: AccessTokenIssuerDep,
) -> TokenResponse:
	access_token = await auth_use_cases.authenticate(
		repo=repo,
		hasher=hasher,
		issuer=issuer,
		username=body.username,
		password=body.password,
	)
	return TokenResponse(access_token=access_token)
