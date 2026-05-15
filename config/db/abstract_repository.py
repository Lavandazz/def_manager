"""
Реализация абстрактного класса для патерна Репозиторий.
Используется для работы с ORM или для  подключения через Postgresql.
Описывает методы для работы с бд
"""

from abc import ABC, abstractmethod


class AbstractRepository(ABC):
    """
    Абстрактный класс для патерна Репозиторий.
    """
    @abstractmethod
    async def add(self, items):
        pass

    @abstractmethod
    async def get(self, id_):
        pass

    @abstractmethod
    async def update(self, id_):
        pass

    @abstractmethod
    async def delete(self, id_):
        pass
