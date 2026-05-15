from sqlalchemy import select
from config.db.abstract_repository import AbstractRepository
from config.db.models import Case


class CaseAlchemyRepository(AbstractRepository):
    """
    Класс для работы с базой данных через SQLAlchemy.
    Запись номером дел в базу данных, получение дел по id, обновление и удаление дел
    """
    def __init__(self, session):
        self.session = session

    async def add(self, items):
        pass

    async def get(self, id_):
        """
        Получение данных из таблицы case по id_case
        """
        return await self.session.get(Case, id_)
    
    async def all_cases(self):
        """
        Получение всех cases не зависимо от фильтров
        """
        stmt = select(Case)
        result = await self.session.execute(stmt)

        return result.scalars().all()
    
    async def get_all_cases_by_user(self, user):
        """
        Получение всех дел, отфильтрованных по пользователю
        """
        stmt = select(Case)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update(self, id_):
        pass

    async def delete(self, id_):
        pass
