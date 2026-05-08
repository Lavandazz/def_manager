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


class ParserSqlAlchemyRepository(AbstractRepository):
    """
    Класс для работы с базой данных через SQLAlchemy.
    Запись документов в базу данных, получение документов по id, обновление и удаление документов,
    полученных из парсера (с сайта КадАрбитр).
    """
    def __init__(self, session):
        self.session = session

    async def add(self, items):
        pass

    async def get(self, id_):
        pass

    async def update(self, id_):
        pass

    async def delete(self, id_):
        pass