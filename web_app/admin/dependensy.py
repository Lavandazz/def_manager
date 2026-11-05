# Создание зависимостей для sqladmin.
# sqladmin не поддерживает зависимости через Fastapi Depends

from sqlalchemy.ext.asyncio import AsyncSession
from shared.core.repository.user_repository import UserAlchemyRepository
from shared.core.services.case_service import CaseService
from shared.core.services.user_service import UserService


def get_user_service(session: AsyncSession) -> UserService:
    repo = UserAlchemyRepository(session)
    return UserService(repo)


def get_case_service(session: AsyncSession) -> CaseService:
    repo = UserAlchemyRepository(session)
    return CaseService(repo)
