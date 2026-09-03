from sqlalchemy import select
from sqlalchemy.orm import selectinload

from config.db.models import Court
from config.logger_config import db_logger

class CourtRepository:
    def __init__(self, session):
        self.session = session

    async def get_or_create_court(self, court_name: str) -> Court:
        """Найти суд по имени или создать новый."""
        existing_court = await self.get_court(court_name)

        if existing_court:
            return existing_court
        
        court = Court(name=court_name)
        self.session.add(court)
        await self.session.commit()
        return court

    async def get_court(self, court_name: str) -> Court | None:
        try:
            stmt = select(Court).where(Court.name == court_name)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()

        except Exception as e:
            await self.session.rollback()
            db_logger.exception("не удалось сохранить дело в бд: %s", e)
            return None