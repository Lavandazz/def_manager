from datetime import timedelta, datetime, timezone
from fastapi import HTTPException
import jwt

from config.schemas.token_schemas import AuthTokenSchema
from config.settings_env import settings


ACCESS_TOKEN_EXPIRE_MINUTES = 60


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
    

    async def verify_token(self, token: str):
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
 