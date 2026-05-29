from fastapi import HTTPException

from app.services.token_service import TokenService
from app.services.user_service import UserService
from app.utils.auth.auth_token import AuthTokenService
from config.db.models import User


class AuthService:
    def __init__(self, token_service: TokenService, auth_token_service: AuthTokenService, user_service: UserService):
        self.token_service = token_service
        self.auth_token_service = auth_token_service
        self.user_service = user_service

    async def get_current_user(self, token: str) -> User:

        if await self.token_service.is_token_black(token):
            raise HTTPException(401, "Токен в черном списке")
        
        # получение данных из токена и извлечение user_id для получения пользователя из БД
        # {'id': 11, 'email': 'my@example.com', 'telegram_id': None, 'exp': 1780048439}
        payload = await self.auth_token_service.verify_token(token)
        user_id = payload.get("id")
        print("payload из токена:", payload, "user_id:", user_id)

        if not user_id:
            raise HTTPException(401, "Неверный токен")
        
        user = await self.user_service.get_user_by_id(user_id)
        print("user из БД:", user, user_id)
        if not user:
            raise HTTPException(401, "Пользователь не найден")
        
        return user