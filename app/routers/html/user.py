from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from core.services.user_service import UserService
from app.utils.dependensy import get_optional_user, get_user_service
from app.utils.auth.password_hasher import PasswordHasher
from config.db.models import User
from config.schemas.user_schemas import UserRegistration, UserSchema, UserUpdateSchema
from config.logger_config import profile_logger


router = APIRouter()

templates = Jinja2Templates(directory="app/templates")

MIN_PASSWORD_LENGTH = 8

@router.get("/profile", tags=["profile"], response_class=HTMLResponse)
async def get_profile(request: Request,
                      user: User = Depends(get_optional_user)):
    """
    Отображение данных пользователя
    :param user: данные берутся из data токена
    :return:
    """

    # Получаем данные из токена
    if not user:
        return templates.TemplateResponse(request, "index.html", context={"message": "Пользователь не авторизован"})
    
    return templates.TemplateResponse(request, "/user/profile.html", {
        "user": user
    })

@router.get("/profile/edit", response_class=HTMLResponse)
async def edit_profile_form(request: Request, 
                            user: User = Depends(get_optional_user),
                            user_service: UserService = Depends(get_user_service),):
    if not user:
        return templates.TemplateResponse(request, "index.html", context={"message": "Пользователь не авторизован"})
    
    needs_setup = PasswordHasher.compare_password(user_hashed_password=user.hashed_password)
    if needs_setup:
        # Сначала нужно установить пароль на отдельной странице
        return RedirectResponse(url="/user/profile/password", status_code=303)

    return templates.TemplateResponse(request, "user/profile_edit.html", {
        "user": user})
        

@router.post("/profile/edit", response_class=HTMLResponse)
async def update_profile(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    telegram_id: int = Form(None),
    password: str = Form(...),
    user: User = Depends(get_optional_user),
    user_service: UserService = Depends(get_user_service)
):
    if not user:
        return templates.TemplateResponse("index.html", {"request": request, "message": "Не авторизован"}, status_code=401)
    
    if not PasswordHasher.verify_password(password, user.hashed_password):
        return templates.TemplateResponse(request, "user/profile_edit.html", {
            "username": username,
            "email": email,
            "telegram_id": telegram_id,
            "error": "Неверный пароль"
        }, status_code=400)
    
    profile_logger.warning("Данные профиля для обновления %s, %s, %s", username, email, telegram_id)
    # Собираем только переданные поля
    update_dict = {}
    if email and user.email != email:
        update_dict["email"] = email
        profile_logger.warning("Добавляю в словарь email %s", update_dict)
    if telegram_id:
        
        update_dict["telegram_id"] = telegram_id if telegram_id != 0 else None
        profile_logger.warning("Добавляю в словарь telegram_id %s", update_dict)

    profile_logger.warning("Передаем словарь!!!! %s", update_dict)
    await user_service.update_user(user, UserUpdateSchema(**update_dict))
    profile_logger.info("Данные профиля обновлены для user_id=%s", user.id)
    
    return RedirectResponse(url="/user/profile", status_code=303)


@router.get("/profile/password", response_class=HTMLResponse)
async def password_form(
    request: Request,
    user: User = Depends(get_optional_user),
    user_service: UserService = Depends(get_user_service),
):
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(request, "user/profile_password.html", {
        "user": user,
        "needs_password_setup": user_service.needs_password_setup(user),
    })


@router.post("/profile/password", response_class=HTMLResponse)
async def update_password(
    request: Request,
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    current_password: str = Form(None),          # None — при первой установке пароля
    user: User = Depends(get_optional_user),
    user_service: UserService = Depends(get_user_service),
):
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    needs_setup = user_service.needs_password_setup(user)
    context = {
        "user": user,
        "needs_password_setup": needs_setup,
    }
    # Валидация
    if len(new_password) < MIN_PASSWORD_LENGTH:
        context["error"] = f"Пароль должен быть не короче {MIN_PASSWORD_LENGTH} символов."
        return templates.TemplateResponse(request, "user/profile_password.html", context, status_code=400)
    if new_password != confirm_password:
        context["error"] = "Новые пароли не совпадают."
        return templates.TemplateResponse(request, "user/profile_password.html", context, status_code=400)
    # Установка или смена
    if needs_setup:
        await user_service.set_password(user, new_password)
    else:
        if not current_password:
            context["error"] = "Введите текущий пароль."
            return templates.TemplateResponse(request, "user/profile_password.html", context, status_code=400)
        ok = await user_service.change_password(user, current_password, new_password)
        if not ok:
            context["error"] = "Неверный текущий пароль."
            return templates.TemplateResponse(request, "user/profile_password.html", context, status_code=400)
    # Письмо об изменении пароля — через Celery
    if user.email:
        print("смена пароля успешнаб письмо отправить на почту", user.email)
        # subject, text, html = build_password_changed_email(user.username)
        # send_message.delay(user.email, subject, text, html)
    profile_logger.info("Пароль обновлён для user_id=%s", user.id)
    return RedirectResponse(url="/user/profile?password_updated=1", status_code=303)


@router.get("/register", response_class=HTMLResponse, tags=["register"])
async def get_register_form(
    request: Request,
        ):
    """
    Отображение формы регистрации пользователя
    """
    return templates.TemplateResponse(request, "user/register.html", {"request": request})



@router.post("/register", tags=["register"], response_class=HTMLResponse)
async def register_user(
    request: Request,
    username: str = Form(...),
    telegram_id: int = Form(None),   
    email: str = Form(...),        
    password: str = Form(...), 
    second_password: str = Form(...),
    user_service: UserService = Depends(get_user_service),
    ):
    """
    Регистрация пользователя.
    валидации данных, получаемых от клиента при регистрации
    Проверяем совпадение паролей, существование пользователя в базе по email и username, хэшируем пароль и сохраняем в базу.
    При успешной регистрации перенаправляем на страницу логина.
    В случае ошибок возвращаем на страницу регистрации. 
    """

    if password != second_password:
        return templates.TemplateResponse(
            request, "user/register.html",
            {"error": "Пароли не совпадают"}
        )

    # Проверяем существование в базе email и username
    # Регистрация новых пользователей только по email
    try:
        existing_user = await user_service.get_user(email=email)

        if existing_user:
            profile_logger.info("Пользователь уже существует: %s`", existing_user)
            return templates.TemplateResponse(
                request, "user/login.html",
                {"error": "Пользователь уже существует"}
            )
        else:
            hashed_password = PasswordHasher.hash_password(password)  # хэш пароля

            user = UserRegistration(
                username=username,
                email=email,
                telegram_id=telegram_id if telegram_id else None,
                password=hashed_password,
                second_password=second_password
            )

            # Сохраняем в бд
            await user_service.create_user(user_data=user)  # сохраняем пользователя в базе данных


            profile_logger.info("Зарегистрирован новый пользователь")

            context = {
                "request": request,
                "title": "Страница входа"
            }
        return templates.TemplateResponse(request, "user/login.html", context)
        
    except Exception as e:
        profile_logger.exception("Ошибка при проверке существования пользователя: %s", e)
        return templates.TemplateResponse(
            request, "user/login.html",
            {"error": "Ошибка сервера"}
        )