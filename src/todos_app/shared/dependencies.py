from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from todos_app.shared.adapters.persistence.database import get_db
from todos_app.shared.settings import Settings, get_settings


DbSessionDep = Annotated[AsyncSession, Depends(get_db)]


def get_settings_dep() -> Settings:
	return get_settings()


SettingsDep = Annotated[Settings, Depends(get_settings_dep)]
