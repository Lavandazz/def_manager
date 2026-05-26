from datetime import timedelta, datetime, timezone

import bcrypt
from fastapi import HTTPException
import jwt

from config.settings_env import settings


ACCESS_TOKEN_EXPIRE_MINUTES = 60


def hash_password(password: str):
    """
    Хэш пароля перед сохранением в БД
    """
    user_pass = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    return user_pass.decode('utf-8')  # Преобразуем хеш в строку для хранения в бд


def verify_password(plain_password, hashed_password):
    """
    Проверка пароля с бд (хэш)
    :param plain_password:
    :param hashed_password:
    :return:
    """
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def create_all_token(data: dict, secret_k: str):
    """
    Создание JSON Web Token
    """
    data_to_encode = data.copy()
    live_time = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    data_to_encode.update({"exp": live_time})  # Добавляем в словарь время жизни токена
    encoded = jwt.encode(data_to_encode, secret_k, algorithm=settings.ALGORITHM)  # Кодируем токен

    return encoded


def create_tokens(user_id: int, email: str, permissions: list):
    """
    Создание основного токена и рефреш
    """
    main_token = create_all_token({
        "user_id": user_id,
        "email": email,
        "permissions": permissions
    }, settings.SECRET_KEY)

    refresh_token = create_all_token({
        "user_id": user_id,
        "email": email
    }, settings.REFRESH_SECRET_KEY)

    return {"main_token": main_token, "refresh_token": refresh_token}


async def decode_jwt(token: str):
    """
    Проверяем JWT-токен и извлекаем пользователя
    """
    try:
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        # Возвращаем айди, email пользователя и его права
        return decoded

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Токен истёк")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Неверный токен")
    