from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status

from app.routers.api.user.schemas import UserLogin, UserRegistration
from app.services.token_service import TokenService
from app.services.user_service import UserService
from app.utils.auth import PasswordHasher
from app.utils.dependensy import get_user_repository
from config.repository.user_repository import UserAlchemyRepository

from config.logger_config import profile_logger


router = APIRouter()


@router.get("/profile", tags=["profile"])
async def get_profile(telegram_id: int,
                      repo: Annotated[UserAlchemyRepository, Depends(get_user_repository)]):
    """
    Для отладки передаем id пользователя.
    В последствии заменить на email
    """
    user_service = UserService(repo)
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
        repo: Annotated[UserAlchemyRepository, Depends(get_user_repository)],
        user: UserRegistration
        ):
    """Регистрация пользователя"""

    if user.password != user.second_password:
        raise HTTPException(status_code=400, detail="Пароли не совпадают")

    user_service = UserService(repo)
    # Проверяем существование в базе email и username
    try:
        existing_user = await user_service.get_user(email=user.email)

        if existing_user:
            raise HTTPException(status_code=400, detail="Пользователь уже существует")
        
        # Раскомментить когда в бд появится поле для хэша пароля и добавится логика сохранения пароля
        # else:
        #     hashed_password = hash_password(password)  # хэш пароля

        #     # Сохраняем в бд
        #     await user_service.create_user(
        #         username=user.username, name=user.name, surname=user.surname, patronymic=user.patronymic, email=user.email, password=hashed_password
        #     )

        profile_logger.info("Зарегистрирован новый пользователь")

        return {"message": "Пользователь зарегистрирован", "user": user.username}
    
    except Exception as e:
        profile_logger.exception("Ошибка при проверке существования пользователя: %s", e)
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e



@router.post("/login", tags=["auth"])
async def login(
    repo: Annotated[UserAlchemyRepository, Depends(get_user_repository)],
    user: UserLogin
    ):
    """Авторизация пользователя.
    Проверяем заполнение всех полей, правильность пароля, существование пользователя в базе.
    """

    if not user.email or not user.password:
        raise HTTPException(status_code=400, detail="Заполните все поля")

    user_service = UserService(repo)
    existing_user = await user_service.get_user(telegram_id=user.telegram_id, email=user.email)

    if not existing_user or not PasswordHasher.verify_password(user.password, existing_user.hashed_password):
        raise HTTPException(status_code=400, detail="Неверно введены логин или пароль")

    return {
        "message": "Успешная авторизация",
        "user": existing_user.username,
        "email": existing_user.email
    }
    # token_service = TokenService(repo)
    # Создаем токен
    # tokens = create_tokens(existing_user.id, existing_user.email)

    # return {
    #     "access_token": tokens["main_token"],
    #     "token_type": "bearer",
    # }