
from sqlalchemy import desc, func, select, update
from sqlalchemy.orm import selectinload
from config.db.abstract_repository import AbstractCaseRepository
from config.db.models import Case, ParsDocument, Debtor
from config.logger_config import db_logger


class CaseAlchemyRepository(AbstractCaseRepository):
    """
    Класс для работы снепосредственно  базой данных через SQLAlchemy.
    Запись номером дел в базу данных, получение дел по id, обновление и удаление дел
    """
    def __init__(self, session):
        self.session = session

    async def add_case(self, case: Case) -> Case | None:
        """
        Сохранение дела в базу данных.
        Передаваемый объект должен быть экземпляром модели Case.
        """
        try:
            self.session.add(case)
            await self.session.commit()
            return case

        except Exception as e:
            db_logger.exception("не удалось сохранить дело в бд: %s", e)
            await self.session.rollback()

    async def get_case(self, case_id):
        """
        Получение данных из таблицы case по id_case
        param: case_id
        """
        stmt = (
            select(Case)
            .where(Case.id == case_id)
            .options(
                selectinload(Case.pars_documents),
                selectinload(Case.debtor),          # сам должник
                selectinload(Case.court_sessions),
                # Подгружаем пользователя
                selectinload(Case.user),
                # счета пользователя

            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_case_documents_paginated(self, case_id: int, page: int, size: int):
        """ Общее количество документов для этого дела (нужно для пагинации)"""
        total_query = select(func.count(ParsDocument.id)).where(ParsDocument.id_case == case_id)
        total_result = await self.session.execute(total_query)
        total_docs = total_result.scalar_one()
        
        # Документы для текущей страницы
        stmt = (
            select(ParsDocument)
            .where(ParsDocument.id_case == case_id)
            .order_by(desc(ParsDocument.date)) # сортировка в обратном порядке по дате
            .offset((page - 1) * size)
            .limit(size)
        )
        result = await self.session.execute(stmt)
        documents = result.scalars().all()
        
        return documents, total_docs

    async def get_cases_by_user(self, user_id):
        """
        Получение всех дел, отфильтрованных по пользователю.
        """
        try:
            stmt = select(Case).where(Case.id_user == user_id).options(selectinload(Case.debtor))
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            db_logger.exception(f"Не получилось отфильтровать дела по пользователю: {e}")


    async def get_cases_by_type(self, user_id, debtor_type):
        """
        Получение всех дел с должниками, с фильтрацией по типу должника.
        Необходимо для отображения на странице дополнения данными физ должников
        """
        stmt = select(Case).join(Case.debtor).where(Case.id_user == user_id, Debtor.debtor_type == debtor_type).options(selectinload(Case.debtor))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    
    async def find_case_by_number(self, number):
        """Получение дела по номеру дела"""
        stmt = select(Case).where(Case.number_case == number)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    
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

    async def delete_case(self, case_id):
        """Мягкое удаление дела. Проставляем статус 1"""
        stmt = update(Case).where(Case.id == case_id, Case.status == 0).values(status=1)
        result = await self.session.execute(stmt)
        # Проверяем, была ли обновлена хотя бы одна запись
        if result.rowcount == 0:
            # Дело не найдено или уже удалено (статус не 0)
            return False
        return True
        


