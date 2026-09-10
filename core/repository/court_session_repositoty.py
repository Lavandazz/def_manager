from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from config.db.abstract_repository import AbstractCourtRepository
from config.db.models import CourtSession
from config.logger_config import db_logger
from config.db.models import Case


class CourtSessionAlchemyRepository(AbstractCourtRepository):
    """
    Класс для работы с непосредственно  базой данных через SQLAlchemy.
    Запись номером дел в базу данных, получение дел по id, обновление и удаление дел
    """
    def __init__(self, session):
        self.session = session

    async def add_court(self, court_session: CourtSession):
        try:
            self.session.add(court_session)
            await self.session.commit()
            return court_session
        except Exception as e:
            db_logger.error("Ошибка сохранения даты, места суда",)

    async def get_courts(self, user_id) -> list[CourtSession]:
        """Поиск заседаний с фильтрацией по пользователю"""
        try:
            stmt = (
            select(CourtSession)
            .join(Case, CourtSession.id_case == Case.id)
            .where(Case.id_user == user_id)
            .options(selectinload(CourtSession.case))
            .order_by(CourtSession.date_court, CourtSession.time_court)
        )
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            db_logger.error("Ошибка при получении списка дат судов", e)


    async def get_court(self, case_id):
        """
        Получение данных(наименования) из таблицы court по id_case
        param: case_id
        """
        try:
            stmt = select(CourtSession).where(CourtSession.id_case == case_id)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        
        except Exception as e:
            db_logger.error("Ошибка при получении даты суда")

    async def exists_court_session(self, case_id: int, court_id: int, date_court: date, time_court: str, hall_court: str) -> bool:
        """Получаение данных о суде для проверки перед сохранением"""
        try:
            stmt = (
                select(CourtSession)
                .where(
                    CourtSession.id_case == case_id,
                    CourtSession.court_id == court_id,
                    CourtSession.date_court == date_court,
                    CourtSession.time_court == time_court,
                    CourtSession.hall_court == hall_court
                )
            )
            db_logger.info("Проверка дат заседаний",)
            result = await self.session.execute(stmt.limit(1))
            return result.scalar() is not None
        except Exception as e:
            db_logger.error(f"Ошибка при проверке даты суда: {e}")
            return False


    async def update(self, param):
        pass

    async def delete(self, date):
        try:
            stmt = select(CourtSession).where(CourtSession.date_court < date)
            result = await self.session.execute(stmt)
            # return result.scalars().delete()
            db_logger.info("На удаление %s старых заседаний суда", result.rowcount)
            return result.scalars().all()
        except Exception as e:
            db_logger.error("Ошибка при удалении даты суда", e)
    