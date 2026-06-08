from pydantic import BaseModel, ConfigDict, Field

from todos_app.domain.users.field_limits import (
	PASSWORD_MAX_LENGTH,
	PASSWORD_MIN_LENGTH,
	USERNAME_MAX_LENGTH,
)


class LoginRequest(BaseModel):
	model_config = ConfigDict(
		extra="forbid",
		json_schema_extra={
			"examples": [
				{
					"username": "jane",
					"password": "changeme",
				}
			]
		},
	)

	username: str = Field(max_length=USERNAME_MAX_LENGTH)
	password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)


class TokenResponse(BaseModel):
	model_config = ConfigDict(
		json_schema_extra={
			"examples": [
				{
					"access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
					"token_type": "bearer",
				}
			]
		},
	)

	access_token: str
	token_type: str = "bearer"
