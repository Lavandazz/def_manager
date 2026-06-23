from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from config.db.abstract_repository import AbstractCaseRepository
from config.db.models import Case, ParsDocument
from config.logger_config import db_logger


class CaseAlchemyRepository(AbstractCaseRepository):
    """
    Класс для работы снепосредственно  базой данных через SQLAlchemy.
    Запись номером дел в базу данных, получение дел по id, обновление и удаление дел
    """
    def __init__(self, session):
        self.session = session

    async def add_case(self, case: Case):
        """
        Сохранение дела в базу данных.
        Передаваемый объект должен быть экземпляром модели Case.
        """
        try:
            self.session.add(case)
            await self.session.commit()
            return case

        except Exception as e:
            await self.session.rollback()
            db_logger.exception("не удалось сохранить дело в бд: %s", e)

    async def get_case(self, case_id):
        """
        Получение данных из таблицы case по id_case
        param: case_id
        """
        stmt = select(Case).where(Case.id == case_id).options(selectinload(Case.pars_documents))
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_case_documents_paginated(self, case_id: int, page: int, size: int):
        # 1. Общее количество документов для этого дела (нужно для пагинации)
        total_query = select(func.count(ParsDocument.id)).where(ParsDocument.id_case == case_id)
        total_result = await self.session.execute(total_query)
        total_docs = total_result.scalar_one()
        
        # 2. Документы для текущей страницы
        stmt = (
            select(ParsDocument)
            .where(ParsDocument.id_case == case_id)
            .offset((page - 1) * size)
            .limit(size)
        )
        result = await self.session.execute(stmt)
        documents = result.scalars().all()
        
        return documents, total_docs

    async def get_cases_by_user(self, user_id):
        """
        Получение всех дел, отфильтрованных по пользователю
        """
        stmt = select(Case).where(Case.id_user == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_cases(self) -> list[Case]:
        """
        Получение всех актуальных номеров дел.
        Case.status == 0 - дело не удалено и считается актуальным
        """
        stmt = select(Case).where(Case.status == 0)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update(self, param):
        pass

    async def delete(self, param):
        pass


