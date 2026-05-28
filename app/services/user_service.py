from config.db.models import User
from config.logger_config import db_logger


class UserService:

    def __init__(self, repository):
        self.repository = repository

    async def create_user(self, username, name, surname, patronymic, email, password, role_name="user") -> User | None:
        pass

    async def get_user(self, telegram_id=None, email=None) -> User | None:
        """
        Проверяем есть ли юзер в базе по уникальному полю telegram_id, email.
        :param telegram_id: передаем для отладки, тк в базе нет данных по email, но в дальнейшем будет использоваться email для получения юзера
        :param email: 
        :return: объект User, если найден, иначе None
        """
        print("получаю юзера", telegram_id, email)
        if telegram_id:
            print("получаю юзера по telegram_id")
            return await self.repository.get_user(telegram_id=telegram_id)
        
        elif email:
            print("получаю юзера по мылу")
            return await self.repository.get_user(email=email)
        
        else:
            print("параметры не верные")
            return None

    async def update_user(self, user):
        pass

    async def delete_user(self, email):
        """
        Мягкое удаление. Помечает пользователя как неактивный
        :param email:
        :return:
        """
        pass
