from sqlalchemy import select, update
from sqlalchemy.orm import joinedload, selectinload

from shared.config.db.abstract_repository import AbstractUserRepository
from shared.config.db.models import MailAddress, User
from shared.config.logger_config import db_logger


class UserAlchemyRepository(AbstractUserRepository):
    """
    Класс для работы с базой данных через SQLAlchemy.
    """
    def __init__(self, session):
        self.session = session

    async def create_user(self, user: User):
        try:
            self.session.add(user)
            await self.session.commit()
            db_logger.info(f"Сохранен новый пользователь {user.username}")
            await self.session.refresh(user)   #  id появится после refresh
            return user # возвращаем объект user, чтобы использовать его данные в ответе

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
                db_logger.debug(f"Пользователь по Telegram ID: {email}")
                return user
            
            elif email:
                db_logger.debug(f"Поиск пользователя по Email: {email}")
                result = await self.session.execute(select(User).where(User.email == email))
                user = result.scalar_one_or_none()
                db_logger.debug("Пользователь по Email: %s", user)
                return user
            
            else:
                db_logger.debug(f"Поиск пользователя по ID: {id}")
                result = await self.session.execute(select(User).where(User.id == id))
                user = result.scalar_one_or_none()
                db_logger.debug(f"Пользователь по ID: {id}, {user}")
                return user
            
        except Exception as e:
            db_logger.exception(f"Ошибка при получении пользователя: {e}")
            return None

    async def get_user_with_profile(self, user_id: int) -> User | None:
            """
            Полный запрос для отображения профиля: подгружает sro, mail_address
            """
            stmt = (
                select(User)
                .where(User.id == user_id)
                .options(
                            joinedload(User.sro),
                            joinedload(User.mail_address)
                                .joinedload(MailAddress.region),
                            joinedload(User.mail_address)
                                .joinedload(MailAddress.address),       
                                )
            )
            result = await self.session.execute(stmt)
            user = result.scalar_one_or_none()
            db_logger.debug(f"get_user_with_profile :{user}")
            return user
    
    async def update_user(self, user: User, user_data):
        try:
            db_logger.debug(f"Данные для обновления пользователя: {user_data}")
            # exclude_unset=True - исключаем поля, которые не были переданы в запросе, чтобы не перезаписывать их значениями по умолчанию

            update_values = user_data.model_dump(exclude_unset=True)
            if not update_values:
                return user

            db_logger.debug("Обновляю поля: %s", update_values)
            stmt = update(User).where(User.id == user.id).values(**update_values)

            await self.session.execute(stmt)
            await self.session.commit()
            await self.session.refresh(user)  # обновляем объект user после коммита, чтобы получить актуальные данные из БД
            db_logger.info(f"Пользователь обновлен: {user}")

            return user # возвращаем обновленного пользователя, чтобы использовать его данные в ответе

        except Exception as e:
            await self.session.rollback()
            db_logger.exception("Ошибка при обновлении пользователя: {e}")

    
    async def delete_user(self, user):
        pass


