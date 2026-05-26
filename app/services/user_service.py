from config.db.models import User
from config.logger_config import db_logger


class UserService:

    def __init__(self, repository):
        self.repository = repository

    async def create_user(self, username, name, surname, patronymic, email, password, role_name="user") -> User | None:
        pass

    async def get_user(self, telegram_id=None, email=None) -> User | None:
        """
        Проверяем есть ли юзер в базе по уникальному полю email
        :param email:
        :return:
        """
        print("emaol", email)
        if email is None:
            print("почты нет")
            return await self.repository.get_user(telegram_id=telegram_id)
        elif email:
            print("получаю юзера по мылу")
            return await self.repository.get_user(email=email)
        

    async def update_user(self, user):
        pass

    async def delete_user(self, email):
        """
        Мягкое удаление. Помечает пользователя как неактивный
        :param email:
        :return:
        """
        pass
