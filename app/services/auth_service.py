from fastapi import HTTPException, Request

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
        """
        Метод для получения текущего пользователя по токену.
        Проверяет токен на валидность и черный список, извлекает данные из токена, получает пользователя из БД и возвращает его.
        В случае ошибок выбрасывает соответствующие HTTP исключения.
        """
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
    
    async def get_user_from_cookie(self, request: Request) -> User:
        """
        Метод для получения текущего пользователя по токену из cookie.
        Извлекает токен из cookie, проверяет его и возвращает пользователя.
        В случае ошибок выбрасывает соответствующие HTTP исключения.
        """
        token = request.cookies.get("access_token")
        if not token:
            print(401, "Токен не найден в cookie")
            return None
        
        return await self.get_current_user(token)