from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status


from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.services.token_service import TokenService
from app.services.user_service import UserService
from app.utils.auth.auth_token import AuthTokenService
from app.utils.auth.password_hasher import PasswordHasher
from app.utils.dependensy import get_token_service, get_user_service

from config.logger_config import profile_logger
from config.schemas.token_schemas import AuthTokenSchema
from config.schemas.user_schemas import UserLogin, UserRegistration


router = APIRouter()


@router.get("/profile", tags=["profile"])
async def get_profile(telegram_id: int,
                      user_service: Annotated[UserService, Depends(get_user_service)]):
    """
    Для отладки передаем id пользователя.
    В последствии заменить на email
    """
    profile_logger.info("Получение данных")
    user = await user_service.get_user(telegram_id=telegram_id)
    if user:
        return {
            "username": user.username,
            "telegram_id": user.telegram_id
        }
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Пользователь не найден')


@router.post("/register", tags=["auth"])


async def register_user(
        user_service: Annotated[UserService, Depends(get_user_service)],
        user: UserRegistration
        ):
    """
    Регистрация пользователя
    :param repo: Используется зависимость от репозитория для работы с таблицей users
    :param user: Используется схема UserRegistration для валидации данных, получаемых от клиента при регистрации
     Проверяем совпадение паролей, существование пользователя в базе по email и username, хэшируем пароль и сохраняем в базу.
     В ответ возвращаем сообщение об успешной регистрации и имя пользователя.
     В случае ошибок возвращаем соответствующие сообщения об ошибках. 
    """

    if user.password != user.second_password:
        raise HTTPException(status_code=400, detail="Пароли не совпадают")

    # Проверяем существование в базе email и username
    # Регистрация новых пользователей только по email
    try:
        existing_user = await user_service.get_user(email=user.email)

        if existing_user:
            profile_logger.info("Пользователь уже существует: %s`", existing_user)
            raise HTTPException(status_code=400, detail="Пользователь уже существует")
        
        else:
            hashed_password = PasswordHasher.hash_password(user.password)  # хэш пароля
            user.password = hashed_password # сохраняем хэш пароля вместо обычного пароля в объекте user, который будет сохранен в базе данных

            # Сохраняем в бд
            await user_service.create_user(user_data=user)  # сохраняем пользователя в базе данных


            profile_logger.info("Зарегистрирован новый пользователь")

            return {"message": "Пользователь зарегистрирован", "user": user.username}
        
    except HTTPException as http_exc:
        profile_logger.warning("Ошибка при регистрации пользователя: %s", http_exc.detail)
        raise http_exc
    
    except Exception as e:
        profile_logger.exception("Ошибка при проверке существования пользователя: %s", e)
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e



@router.post("/login", tags=["auth"])
async def login(
    user_service: Annotated[UserService, Depends(get_user_service)],
    user: UserLogin
    ):
    """
    Авторизация пользователя.
    :param user_service: Используется зависимость от сервиса для работы с логикой авторизации.
    :param user: Используется схема UserLogin для валидации данных, получаемых от клиента при авторизации.
    Проверяем наличие email и password, существование пользователя в базе по email, совпадение пароля с хэшем в базе, создаем JWT-токен и возвращаем его клиенту вместе с сообщением об успешной авторизации и именем пользователя.
    В случае ошибок возвращаем соответствующие сообщения об ошибках.
    """

    if not user.email or not user.password:
        raise HTTPException(status_code=400, detail="Заполните все поля")

    existing_user = await user_service.get_user(telegram_id=user.telegram_id, email=user.email)

    if not existing_user or not PasswordHasher.verify_password(user.password, existing_user.hashed_password):
        raise HTTPException(status_code=400, detail="Неверно введены логин или пароль")

    auth = AuthTokenService()
    # Создаем токен
    token = auth.create_token(data=AuthTokenSchema(id=existing_user.id, email=existing_user.email))
    refresh_token = auth.create_token(data=AuthTokenSchema(id=existing_user.id, email=existing_user.email), is_refresh=True)
    
    print("созданные токены:", token, refresh_token)

    return {
        "message": "Успешная авторизация",
        "user": existing_user.username,
        "email": existing_user.email,
        "access_token": token,
        "token_type": "bearer",
    }


@router.post("/logout", tags=["auth"])
async def logout(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
                 token_service: TokenService = Depends(get_token_service)):
    """Выход из системы - добавление токена в черный список и деактивация"""
    token = credentials.credentials
    await token_service.add_token(token=token)

    return {"message": "Успешный выход из системы"}