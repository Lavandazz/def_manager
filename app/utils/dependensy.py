from typing import Annotated
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from fastapi import Depends, Request


from app.services.auth_service import AuthService
from app.services.case_service import CaseService
from app.services.token_service import TokenService
from app.services.user_service import UserService

from app.utils.auth.auth_token import AuthTokenService
from config.db.models import User
from config.repository.case_repository import CaseAlchemyRepository
from config.db.database import UnitOfWork
from config.repository.token_repository import TokenAlchemyRepository
from config.repository.user_repository import UserAlchemyRepository
from config.settings_env import settings

security = HTTPBearer()

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


async def get_auth_token_service() -> AuthTokenService:
    return AuthTokenService()


async def get_verify_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    token_service=Depends(get_token_service),
    auth_token_service=Depends(get_auth_token_service),
    user_service=Depends(get_user_service),
) -> User:
    """ Функция для DI в api сервисах,
    Получаем токен из заголовка, проверяем его и возвращаем текущего пользователя"""
    auth = AuthService(token_service, auth_token_service, user_service)

    return await auth.get_current_user(credentials.credentials) # предаем токен из заголовка в метод get_current_user сервиса AuthService, который проверяет токен и возвращает текущего пользователя или выбрасывает исключение при ошибке проверки.


async def get_optional_user(
    request: Request,
    token_service=Depends(get_token_service),
    auth_token_service=Depends(get_auth_token_service),
    user_service=Depends(get_user_service),):
    """ Функция для DI в html роутерах"""
    auth = AuthService(token_service, auth_token_service, user_service)
    # предаем токен из заголовка в метод get_current_user сервиса AuthService, который проверяет токен и возвращает текущего пользователя 
    # или выбрасывает исключение при ошибке проверки.

    return await auth.get_user_from_cookie(request) 

