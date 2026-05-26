from sqlalchemy import select
from config.db.abstract_repository import AbstractCaseRepository
from config.db.models import Case


class CaseAlchemyRepository(AbstractCaseRepository):
    """
    Класс для работы снепосредственно  базой данных через SQLAlchemy.
    Запись номером дел в базу данных, получение дел по id, обновление и удаление дел
    """
    def __init__(self, session):
        self.session = session

    async def add(self, param):
        pass

    async def get(self, param):
        """
        Получение данных из таблицы case по id_case
        param: 
        """
        return await self.session.get(Case, param)
    
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
        stmt = select(Case).where(Case.id_user == user.id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update(self, param):
        pass

    async def delete(self, param):
        pass


