from config.db.models import User
from config.schemas.user_schemas import UserRegistration, UserSchema


class UserService:

    def __init__(self, repository):
        self.repository = repository

    async def create_user(self, user_data: UserRegistration) -> User | None:

        new_user = User(
                username=user_data.username,
                email=user_data.email,
                hashed_password=user_data.password,
                telegram_id=user_data.telegram_id
            )
        await self.repository.create_user(new_user)

    async def get_user(self, telegram_id=None, email=None) -> User | None:
        """
        Проверяем есть ли юзер в базе по уникальному полю telegram_id, email.
        :param telegram_id: передаем для отладки, тк в базе нет данных по email, но в дальнейшем будет использоваться email для получения юзера
        :param email: 
        :return: объект User, если найден, иначе None
        """
        if telegram_id:
            return await self.repository.get_user(telegram_id=int(telegram_id))
        
        elif email:
            return await self.repository.get_user(email=email)
        
        else:
            return None
        
    async def get_user_by_id(self, user_id) -> User | None:
        """
        Получаем юзера по id для проверки токена и получения данных юзера из БД при авторизации
        :param user_id: id пользователя, извлекаемый из токена
        :return: объект User, если найден, иначе None
        """
        return await self.repository.get_user(id=user_id)
    
    async def get_user_by_name(self, username) -> User | None:
        """
        Только для разработки, ускорение авторизации
        """
        return await self.repository.get_user_by_name(username=username)

    async def update_user(self, user: User, user_data: UserSchema):
        return await self.repository.update_user(user, user_data)

    async def delete_user(self, email):
        """
        Мягкое удаление. Помечает пользователя как неактивный
        :param email:
        :return:
        """
        pass
