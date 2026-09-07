"""
Реализация абстрактного класса для патерна Репозиторий.
Используется для работы с ORM или для  подключения через Postgresql.
Описывает методы для работы с бд
"""

from abc import ABC, abstractmethod

from config.db.models import Debtor, User, Case
from config.schemas.user_schemas import UserSchema


class AbstractCaseRepository(ABC):
    """
    Абстрактный класс для патерна Репозиторий.
    """
    @abstractmethod
    async def add_case(self, case: Case) -> Case | None:
        pass

    @abstractmethod
    async def get_case(self, case_id: int) -> Case:
        pass

    @abstractmethod
    async def get_cases(self) -> list[Case]:
        pass

    @abstractmethod
    async def update(self, param):
        pass

    @abstractmethod
    async def delete_case(self, case_id: int) -> bool:
        pass


class AbstractCourtRepository(ABC):
    """
    Абстрактный класс для патерна Репозиторий.
    """
    @abstractmethod
    async def add_court(self, court_session):
        pass

    @abstractmethod
    async def get_courts(self, user_id):
        pass

    @abstractmethod
    async def update(self, param):
        pass

    @abstractmethod
    async def delete(self, date):
        pass


class AbstractTokenRepository(ABC):
    """
    Абстрактный класс для патерна Репозиторий.
    """
    @abstractmethod
    async def add_token(self, token):
        pass

    @abstractmethod
    async def exists(self, token) -> bool:
        pass

    @abstractmethod
    async def delete(self, token):
        pass


class AbstractUserRepository(ABC):
    """
    Абстрактный класс для патерна Репозиторий.
    """
    @abstractmethod
    async def create_user(self, user: User):
        pass

    @abstractmethod
    async def get_user(self,telegram_id=None, email=None) -> User | None:
        pass

    @abstractmethod
    async def update_user(self, user: User, user_data: UserSchema) -> User | None:
        pass

    @abstractmethod
    async def delete_user(self, user: User):
        pass


class AbstractDebtorRepository(ABC):
    """
    Абстрактный класс для патерна Репозиторий.
    """
    @abstractmethod
    async def add_debtor(self, debtor: Debtor) -> Debtor:
        pass

    @abstractmethod
    async def get_debtor(self, debtor_id: int) -> Debtor:
        pass

    @abstractmethod
    async def update_debtor(self, debtor: Debtor) -> Debtor:
        pass

    @abstractmethod
    async def delete_debtor(self, debtor_id) -> bool:
        pass


    