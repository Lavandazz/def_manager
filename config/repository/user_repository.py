from sqlalchemy import select

from config.db.abstract_repository import AbstractUserRepository
from config.db.models import User
from config.logger_config import db_logger


class UserAlchemyRepository(AbstractUserRepository):
    """
    Класс для работы с базой данных через SQLAlchemy.
    """
    def __init__(self, session):
        self.session = session

    async def create_user(self, user: User):
        print("сохраняю юзера", user)
        try:
            self.session.add(user)
            await self.session.commit()
        except Exception as e:
            await self.session.rollback()
            db_logger.exception("не удалось сохранить токен в бд: %s", e)

    async def get_user(self, telegram_id=None, email=None):
        """
        Получение пользователя по полю email.
        email=None для того, что в первом входе в базе нет данных об email (для теста базы)
        """
        try:
            if email is None:
                result = await self.session.execute(select(User).where(User.telegram_id == telegram_id))
                user = result.scalar_one_or_none()
                db_logger.debug("Пользователь по Telegram ID: %s", user)
                return user
            else:
                db_logger.debug("Поиск пользователя по Email: %s", email)
                result = await self.session.execute(select(User).where(User.email == email))
                user = result.scalar_one_or_none()
                db_logger.debug("Пользователь по Email: %s", user)
                return user
            
        except Exception as e:
            db_logger.exception("Ошибка при получении пользователя: %s", e)
            return None
        

    async def update_user(self, user):
        pass

    
    async def delete_user(self, user):
        pass


