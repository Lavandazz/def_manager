from datetime import timedelta, datetime, timezone

import bcrypt
from fastapi import HTTPException
import jwt

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
        print("проверка пароля", plain_password, hashed_password)
        return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


class AuthService:
    """
    Класс для создания и проверки JWT-токенов."""

    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.refresh_secret_key = settings.REFRESH_SECRET_KEY

    def create_all_token(self, data: dict, secret_k: str):
        """
        Создание JSON Web Token
        """
        data_to_encode = data.copy()
        live_time = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        data_to_encode.update({"exp": live_time})  # Добавляем в словарь время жизни токена
        encoded = jwt.encode(data_to_encode, secret_k, algorithm=settings.ALGORITHM)  # Кодируем токен

        return encoded


    def create_tokens(self, user_id: int, email: str):
        """
        Создание основного токена и рефреш
        """
        main_token = self.create_all_token({
            "user_id": user_id,
            "email": email,
        }, self.secret_key)

        refresh_token = self.create_all_token({
            "user_id": user_id,
            "email": email
        }, self.refresh_secret_key)

        return {"main_token": main_token, "refresh_token": refresh_token}


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
        