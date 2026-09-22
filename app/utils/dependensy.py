from typing import Annotated
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from config.db.db_config import get_db
from fastapi import Depends, Request

from core.repository.account_repository import AccountRepository
from core.repository.address_repository import AddressRepository, ResidentialAddressRepository
from core.repository.bank_repository import BankRepository
from core.repository.debtor_repository import DebtorAlchemyRepository
from core.repository.region_repository import RegionRepository
from core.services.account_service import AccountService
from core.services.address_service import AddressService, MailAddressService, ResidentialAddressService
from core.services.auth_service import AuthService
from core.services.bank_service import BankService
from core.services.case_service import CaseService
from core.services.court_session_service import CourtSessionService
from core.services.debtor_service import DebtorService
from core.services.region_service import RegionService
from core.services.token_service import TokenService
from core.services.user_service import UserService

from app.utils.auth.auth_token import AuthTokenService
from config.db.models import User
from core.repository.case_repository import CaseAlchemyRepository
from config.db.database import UnitOfWork
from core.repository.court_session_repositoty import CourtSessionAlchemyRepository
from core.repository.token_repository import TokenAlchemyRepository
from core.repository.user_repository import UserAlchemyRepository


security = HTTPBearer()



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

async def get_region_repo(unit_of_work: Annotated[UnitOfWork, Depends(get_db)]) -> RegionRepository:
    return RegionRepository(unit_of_work.session)


async def get_region_service(repo: RegionRepository = Depends(get_region_repo)) -> RegionService:
    return RegionService(repo)


async def get_residential_address_repo(unit_of_work: Annotated[UnitOfWork, Depends(get_db)]) -> ResidentialAddressRepository:
    return ResidentialAddressRepository(unit_of_work.session)


async def get_residential_address_service(repo: ResidentialAddressRepository = Depends(get_residential_address_repo)) -> ResidentialAddressService:
    return ResidentialAddressService(repo)

async def get_debtor_repository(unit_of_work: Annotated[UnitOfWork, Depends(get_db)]):
    """
    Функция для DI в api сервисах,
    """
    return DebtorAlchemyRepository(unit_of_work.session) # передаем сессию


async def  get_address_repo(unit_of_work: Annotated[UnitOfWork, Depends(get_db)]) -> AddressRepository:
    return AddressRepository(unit_of_work.session)

async def get_address_service(repo: AddressRepository = Depends(get_residential_address_repo)) -> AddressService:
    return AddressService(repo)


async def get_mail_service(region_service: RegionService = Depends(get_region_service),
                           address_service: AddressService = Depends(get_address_service)):
    return MailAddressService(region_service, address_service)

async def get_bank_repository(unit_of_work: Annotated[UnitOfWork, Depends(get_db)]) -> BankRepository:
    return BankRepository(unit_of_work.session)


async def get_bank_service(repo: BankRepository = Depends(get_bank_repository),
                          mail_service: MailAddressService = Depends(get_mail_service)) -> BankService:
    return BankService(repo, mail_service)


async def get_account_repository(unit_of_work: Annotated[UnitOfWork, Depends(get_db)]) -> AccountRepository:
    return AccountRepository(unit_of_work.session)


async def get_account_service(
        repo: AccountRepository = Depends(get_account_repository), 
        bank_service: BankService = Depends(get_bank_service)) -> AccountService:
    return AccountService(repo, bank_service)


async def get_debtor_service(
        repository: DebtorAlchemyRepository = Depends(get_debtor_repository),
        region_service: RegionService = Depends(get_region_service),
        address_service: AddressService = Depends(get_address_service),
        residential_service: ResidentialAddressService = Depends(get_residential_address_service),
        account_service: AccountService = Depends(get_account_service)):
    """
    Функция для DI в api сервисах.
    Для работы с сервисом Должников, передаем сервисы региона и адреса, 
    так как должник связан с этими таблицами в бд.
    При сохранении должника, будут использоваться эти сервисы.
    """
    service = DebtorService(
        repository=repository,
        region_service=region_service,
        address_service=address_service,
        residential_service=residential_service,
        account_service=account_service)
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


async def get_court_repository(unit_of_work: Annotated[UnitOfWork, Depends(get_db)]):
    """
    Функция для DI в api сервисах,
    например, в эндпоинте получаем репозиторий и работаем с сервисом,
    court_service = CourtSessionService(repo)
    """
    return CourtSessionAlchemyRepository(unit_of_work.session)


async def get_court_service(court_repo: Annotated[CourtSessionAlchemyRepository, Depends(get_court_repository)]):
    """
    Функция для DI в api сервисах,
    Получаем сессию и работаем с сервисом,
    court_service = CourtSessionService(session)
    """
    service = CourtSessionService(court_repo)
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
