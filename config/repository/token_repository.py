from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from config.db.abstract_repository import AbstractTokenRepository
from config.db.models import BlackListToken
from config.logger_config import db_logger


class TokenAlchemyRepository(AbstractTokenRepository):
    """
    Класс для работы с черным списком токенов в базе данных через SQLAlchemy.
    Сохранение токена в черный список, проверка наличия токена в черном списке
    """

    def __init__(self, session):
        self.session = session

    async def add(self, token: str) -> None:
        try:
            self.session.add(BlackListToken(token=token))
            await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            db_logger.exception("не удалось сохранить токен в бд: %s", e)

    async def exists(self, token: str) -> bool:
        try:
            result = await self.session.execute(
                select(BlackListToken).where(BlackListToken.token == token)
            )
            return result.scalar_one_or_none() is not None
        except SQLAlchemyError as e:
            db_logger.exception("Ошибка проверки токена: %s", e)
            return False

    async def delete(self, token):
        pass
