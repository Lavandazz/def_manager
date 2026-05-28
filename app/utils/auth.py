from datetime import timedelta, datetime, timezone

import bcrypt
from fastapi import HTTPException
import jwt

from app.services.token_service import TokenService
from config.schemas.token_schemas import AuthTokenSchema
from config.settings_env import settings


ACCESS_TOKEN_EXPIRE_MINUTES = 60


class PasswordHasher:
    """
    Класс для хэширования паролей и проверки паролей.
    """

    @staticmethod
    def hash_password(password: str):
        """
        Хэширование пароля перед сохранением в БД
        :param password: пароль, который ввел пользователь
        :return: хэш пароля для сохранения в бд
        """
        user_pass = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        return user_pass.decode('utf-8')  # Преобразуем хеш в строку для хранения в бд

    @staticmethod
    def verify_password(plain_password, hashed_password):
        """
        Проверка пароля с бд (хэш)
        :param plain_password: пароль, который ввел пользователь
        :param hashed_password: пароль, который хранится в бд (хэш)
        :return: True, если пароль верный, иначе False
        """
        return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


class AuthTokenService:
    """
    Класс для создания и проверки JWT-токенов."""

    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.refresh_secret_key = settings.REFRESH_SECRET_KEY

    def create_token(self, data: AuthTokenSchema, is_refresh: bool = False) -> str:
        """
        :param data: данные для создания токена (id, email, telegram_id)
        :param is_refresh: флаг, указывающий, является ли токен рефреш-токеном
        :return: сгенерированный JWT-токен
        """
        data_to_encode = data.dict()
        live_time = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        data_to_encode.update({"exp": live_time})  # Добавляем в словарь время жизни токена
        if is_refresh:
            encoded = jwt.encode(data_to_encode, self.refresh_secret_key, algorithm=settings.ALGORITHM)  # Кодируем токен
        else:
            encoded = jwt.encode(data_to_encode, self.secret_key, algorithm=settings.ALGORITHM)  # Кодируем токен
        print("новые  токен:", encoded)
        return encoded
    

    async def decode_jwt(self, token: str):
        """
        Проверяем JWT-токен и извлекаем пользователя
        """
        try:
            decoded = jwt.decode(token, self.secret_key, algorithms=[settings.ALGORITHM])
            # Возвращаем айди, email пользователя
            return decoded

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Токен истёк")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Неверный токен")
        