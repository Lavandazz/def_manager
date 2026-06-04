"""
Реализация абстрактного класса для патерна Репозиторий.
Используется для работы с ORM или для  подключения через Postgresql.
Описывает методы для работы с бд
"""

from abc import ABC, abstractmethod

from config.db.models import User


class AbstractCaseRepository(ABC):
    """
    Абстрактный класс для патерна Репозиторий.
    """
    @abstractmethod
    async def add_case(self, param):
        pass

    @abstractmethod
    async def get_case(self, case_id):
        pass

    @abstractmethod
    async def update(self, param):
        pass

    @abstractmethod
    async def delete(self, param):
        pass


class AbstractCourtRepository(ABC):
    """
    Абстрактный класс для патерна Репозиторий.
    """
    @abstractmethod
    async def add_court(self, param):
        pass

    @abstractmethod
    async def get_all_courts(self, user_id):
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
    async def update_user(self, user: User, user_data):
        pass

    @abstractmethod
    async def delete_user(self, user: User):
        pass