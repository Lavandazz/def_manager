from typing import Annotated
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from fastapi import Depends, HTTPException

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


async def verify_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        token_service: TokenService = Depends(get_token_service),
        auth_token: AuthTokenService = Depends(get_auth_token_service),
        user_service: UserService = Depends(get_user_service),
        ):
    """Проверка токена"""
    # берем токен из заголовка
    print("извлекаю токен из заголовка")
    token = credentials.credentials
    
    if await token_service.is_token_black(token):
        raise HTTPException(status_code=401, detail="Токен в черном списке")

    try:

        token_data = await auth_token.verify_token(token)  # получаем данные из токена
        print("token извлеченные данные:", token_data)
        user_email = token_data["email"]  # извлекаем email пользователя из данных  токена
        user_telegram = token_data["telegram_id"]  # извлекаем telegram_id пользователя из данных  токена

        if user_email:
            user = await user_service.get_user(email=user_email)  # получаем пользователя из БД по email из токена
        else:
            user = await user_service.get_user(telegram_id=user_telegram)

        if user:
            return user

    except HTTPException:
        raise HTTPException(status_code=401, detail="Неверный токен")
    
    
async def get_verify_user(user: User = Depends(verify_user)):
    return user

