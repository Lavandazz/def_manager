from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from shared.config.db.db_config import async_sessionmaker
from web_app.admin.dependensy import get_user_service
from web_app.utils.auth.auth_token import AuthTokenService
from web_app.utils.auth.password_hasher import PasswordHasher



class AdminAuth(AuthenticationBackend):
    """Авторизация админа в sqladmin"""
    def __init__(self, secret_key: str, session_maker: async_sessionmaker):
        super().__init__(secret_key)
        self.session_maker = session_maker

    async def login(self, request: Request) -> bool:
        if request.method != "POST":
            return False  # GET на /admin/login просто показывает форму

        form = await request.form()
        email = form.get("username") # sqladmin это поле "username"
        password = form.get("password")

        if not email or not password:
            return False


        # Получаем пользователя 
        # открываем сессию из того же session_maker, что и у Admin
        async with self.session_maker() as session:
            user_service = get_user_service(session)
            user = await user_service.get_user(email=email)
            if user is None:
                return False
            user_id = user.id

         # Проверяем пароль 
        if not PasswordHasher.verify_password(password, user.hashed_password):
            return False

        request.session.update({"user_id": user_id})
        return True


    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return request.session.get("user_id") is not None