from sqlalchemy import select, update

from config.db.abstract_repository import AbstractUserRepository
from config.db.models import User
from config.logger_config import db_logger
from config.schemas.user_schemas import UserSchema


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

    async def get_user(self, telegram_id=None, email=None, id=None) -> User | None:
        """
        Получение пользователя по полю email.
        email=None для того, что в первом входе в базе нет данных об email (для теста базы)
        """
        try:
            if telegram_id:
                result = await self.session.execute(select(User).where(User.telegram_id == telegram_id))
                user = result.scalar_one_or_none()
                db_logger.debug("Пользователь по Telegram ID: %s", user)
                return user
            
            elif email:
                db_logger.debug("Поиск пользователя по Email: %s", email)
                result = await self.session.execute(select(User).where(User.email == email))
                user = result.scalar_one_or_none()
                db_logger.debug("Пользователь по Email: %s", user)
                return user
            
            else:
                db_logger.debug("Поиск пользователя по ID: %s", id)
                result = await self.session.execute(select(User).where(User.id == id))
                user = result.scalar_one_or_none()
                db_logger.debug("Пользователь по ID: %s", user)
                return user
            
        except Exception as e:
            db_logger.exception("Ошибка при получении пользователя: %s", e)
            return None
        
    async def get_user_by_name(self, username) -> User | None:
        """
        Только для разработки, ускорение авторизации
        """
        result = await self.session.execute(select(User).where(User.username==username))
        user = result.scalar_one_or_none()
        db_logger.debug("Пользователь по username: %s", user)
        return user
    
    async def update_user(self, user: User, user_data: UserSchema):
        try:
            db_logger.info("Принимял данные для обновления: %s", user_data)
            # exclude_unset=True - исключаем поля, которые не были переданы в запросе, чтобы не перезаписывать их значениями по умолчанию

            update_values = user_data.model_dump(exclude_unset=True)
            if not update_values:
                return user

            db_logger.info("Обновляю поля: %s", update_values)
            stmt = update(User).where(User.id == user.id).values(**update_values)

            await self.session.execute(stmt)
            await self.session.commit()
            await self.session.refresh(user)  # обновляем объект user после коммита, чтобы получить актуальные данные из БД
            db_logger.info("Пользователь обновлен: %s", user)

            return user # возвращаем обновленного пользователя, чтобы использовать его данные в ответе

        except Exception as e:
            await self.session.rollback()
            db_logger.exception("Ошибка при обновлении пользователя: %s", e)

    
    async def delete_user(self, user):
        pass


