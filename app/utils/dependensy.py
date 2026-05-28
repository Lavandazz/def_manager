from typing import Annotated
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from fastapi import Depends



from app.services.case_service import CaseService
from app.services.token_service import TokenService
from app.services.user_service import UserService
from config.repository.case_repository import CaseAlchemyRepository
from config.db.database import UnitOfWork
from config.repository.token_repository import TokenAlchemyRepository
from config.repository.user_repository import UserAlchemyRepository
from config.settings_env import settings


ADB_URL = settings.get_async_db_url()
engine = create_async_engine(url=ADB_URL)
async_sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)


async def get_db():
    unit_of_work = UnitOfWork(async_sessionmaker)
    async with unit_of_work:
        yield unit_of_work

async def get_case_repository(unit_of_work: Annotated[UnitOfWork, Depends(get_db)]):
    """
    Функция для DI в api сервисах,
    например, в эндпоинте получаем репозиторий и работаем с сервисом,
    cases_service = CaseService(repo)
    """
    return CaseAlchemyRepository(unit_of_work.session)

async def get_case_service(case_repo: Annotated[CaseAlchemyRepository, Depends(get_case_repository)]):
    """
    Функция для DI в api сервисах,

    """
    service = CaseService(case_repo)
    return service



async def get_token_repository(unit_of_work: Annotated[UnitOfWork, Depends(get_db)]):
    """
    Функция для DI в api сервисах,
    например, в эндпоинте получаем репозиторий и работаем с сервисом,
    token_service = TokenService(repo)
    """
    return TokenAlchemyRepository(unit_of_work.session)

async def get_token_service(token_repo: Annotated[TokenAlchemyRepository, Depends(get_token_repository)]):
    """
    Функция для DI в api сервисах,
    Получаем сессию и работаем с сервисом,
    token_service = TokenService(session)
    """
    service = TokenService(token_repo)
    return service


async def get_user_repository(unit_of_work: Annotated[UnitOfWork, Depends(get_db)]):
    """
    Функция для DI в api сервисах,
    например, в эндпоинте получаем репозиторий и работаем с сервисом,
    token_service = TokenService(repo)
    """
    return UserAlchemyRepository(unit_of_work.session)

async def get_user_service(user_repo: Annotated[UserAlchemyRepository, Depends(get_user_repository)]):
    """
    Функция для DI в api сервисах,
    Получаем сессию и работаем с сервисом,
    user_service = UserService(session)
    """
    service = UserService(user_repo)
    return service
