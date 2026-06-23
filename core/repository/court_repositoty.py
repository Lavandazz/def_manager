from sqlalchemy import select
from sqlalchemy.orm import selectinload

from config.db.abstract_repository import AbstractCourtRepository
from config.db.models import CourtSession
from config.logger_config import db_logger
from config.db.models import Case


class CourtAlchemyRepository(AbstractCourtRepository):
    """
    Класс для работы снепосредственно  базой данных через SQLAlchemy.
    Запись номером дел в базу данных, получение дел по id, обновление и удаление дел
    """
    def __init__(self, session):
        self.session = session

    async def add_court(self, param):
        pass

    async def get_all_courts(self, user_id) -> list[CourtSession]:
        db_logger.info("Поиск заседаний")

        stmt = (
        select(CourtSession)
        .join(Case, CourtSession.id_case == Case.id)
        .where(Case.id_user == user_id)
        .options(selectinload(CourtSession.case))
        .order_by(CourtSession.date_court, CourtSession.time_court)
    )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_court_by_case(self, case_id):
        """
        Получение данных из таблицы court по id_case
        param: case_id
        """
        stmt = select(CourtSession).where(CourtSession.id_case == case_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update(self, param):
        pass

    async def delete(self, date):
        stmt = select(CourtSession).where(CourtSession.date_court < date)
        result = await self.session.execute(stmt)
        # return result.scalars().delete()
        db_logger.info("На удаление %s старых заседаний суда", result.rowcount)
        return result.scalars().all()
    