import asyncio

from click.core import V
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import ValidationError

from web_app.utils.caches_data import get_cases_from_cache
from web_app.utils.bank_helper import to_date_or_none, to_int_or_none
from web_app.web_conf import templates

from shared.celery_tasks.task_manager import send_verification_email, start_efrsb_parsing
from shared.core.services.address_service import MailAddressService
from shared.core.services.redis_service import RedisService
from shared.core.services.user_service import UserService
from web_app.utils.dependensy import get_mail_service, get_optional_user, get_redis_service, get_user_service
from web_app.utils.auth.password_hasher import PasswordHasher
from shared.config.db.models import User
from shared.config.schemas.user_schemas import UserRegistration, UserUpdateSchema
from shared.config.logger_config import profile_logger

from shared.utils.exceptions import VerificationCodeAlreadySent


router = APIRouter()


MIN_PASSWORD_LENGTH = 8


def _clean_str(value: str | None, max_len: int = 255) -> str | None:
    """Обрезка и ограничение длины текстового поля формы."""
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    return cleaned[:max_len]


@router.get("/profile", tags=["profile"], response_class=HTMLResponse)
async def get_profile(request: Request,
                      user_service: UserService = Depends(get_user_service),
                      user: User = Depends(get_optional_user)):
    """
    Отображение данных пользователя
    :param user: данные берутся из data токена
    :return:
    """
    # Получаем данные из токена
    if not user:
        return templates.TemplateResponse(request, "index.html", context={"message": "Пользователь не авторизован"})

    user_profile = await user_service.get_user_profile(user_id=user.id)
    context = {
        "request": request,
        "title": "Профиль",}
    
    if user:
        cases = await get_cases_from_cache(user_id=user.id) # получение кэша
        context["cases"] = cases
  
    context["user"] = user_profile
    return templates.TemplateResponse(request, "/user/profile.html", context=context)

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

    user_profile = await user_service.get_user_profile(user_id=user.id)
    return templates.TemplateResponse(request, "user/profile_edit.html", {
        "user": user_profile,
        "needs_password_setup": False,
    })
        

@router.post("/profile/edit", response_class=HTMLResponse)
async def update_profile(
    request: Request,
    username: str = Form(""),
    email: str = Form(""),
    telegram_id: str = Form(""),
    inn: str = Form(""),
    snils: str = Form(""),
    reg_num: str = Form(""),
    reg_date: str = Form(""),
    date_begin: str = Form(""),
    mail_index: str = Form(""),
    region_name: str = Form(""),
    city: str = Form(""),
    street: str = Form(""),
    house: str = Form(""),
    building: str = Form(""),
    password: str = Form(""),
    user: User = Depends(get_optional_user),
    user_service: UserService = Depends(get_user_service),
    mail_service: MailAddressService = Depends(get_mail_service),
):
    if not user:
        return templates.TemplateResponse(
            request, "index.html",
            {"message": "Не авторизован"},
            status_code=401,
        )

    user_profile = await user_service.get_user_profile(user_id=user.id)

    # Значения формы для повторного показа при ошибке (Jinja экранирует вывод)
    form_values = {
        "username": username,
        "email": email,
        "telegram_id": telegram_id,
        "inn": inn,
        "snils": snils,
        "reg_num": reg_num,
        "reg_date": reg_date,
        "date_begin": date_begin,
        "mail_index": mail_index,
        "region_name": region_name,
        "city": city,
        "street": street,
        "house": house,
        "building": building,
    }

    def _error_response(message: str, status_code: int = 400):
        return templates.TemplateResponse(
            request,
            "user/profile_edit.html",
            {
                "user": user_profile,
                "form": form_values,
                "needs_password_setup": False,
                "error": message,
            },
            status_code=status_code,
        )

    # Без пароля в БД ничего не пишем
    if not (password or "").strip():
        return _error_response("Введите пароль для подтверждения изменений")

    if not PasswordHasher.verify_password(password, user.hashed_password):
        return _error_response("Неверный пароль")

    cleaned_username = _clean_str(username, 150)
    cleaned_email = _clean_str(email, 254)
    cleaned_inn = _clean_str(inn, 12)
    cleaned_snils = _clean_str(snils, 14)
    cleaned_reg_num = _clean_str(reg_num, 50)

    try:
        parsed_reg_date = to_date_or_none(reg_date)
        parsed_date_begin = to_date_or_none(date_begin)
        parsed_telegram = to_int_or_none(telegram_id)
        cleaned_mail_index = to_int_or_none(mail_index)
    except ValueError:
        return _error_response("Проверьте корректность числовых полей и дат")

    cleaned_region = _clean_str(region_name, 150)
    cleaned_city = _clean_str(city, 150)
    cleaned_street = _clean_str(street, 200)
    cleaned_house = _clean_str(house, 50)
    cleaned_building = _clean_str(building, 50)

    address_parts = [
        cleaned_mail_index,
        cleaned_region,
        cleaned_city,
        cleaned_street,
        cleaned_house,
        cleaned_building,
    ]
    address_started = any(part is not None for part in address_parts)

    mail_address_id = None
    if address_started:
        if cleaned_mail_index is None or not cleaned_city or not cleaned_street or not cleaned_house:
            return _error_response(
                "Для почтового адреса укажите индекс, город, улицу и дом"
            )
        mail = await mail_service.create_mail_address(
            mail_index=cleaned_mail_index,
            city=cleaned_city,
            street=cleaned_street,
            house=cleaned_house,
            building=cleaned_building,
            region_name=cleaned_region,
        )
        mail_address_id = mail.id

    update_dict: dict = {}
    if cleaned_username is not None:
        update_dict["username"] = cleaned_username
    if cleaned_email is not None:
        update_dict["email"] = cleaned_email
    if telegram_id.strip() != "":
        update_dict["telegram_id"] = parsed_telegram
    update_dict["inn"] = cleaned_inn
    update_dict["snils"] = cleaned_snils
    update_dict["reg_num"] = cleaned_reg_num
    update_dict["reg_date"] = parsed_reg_date
    update_dict["date_begin"] = parsed_date_begin
    if mail_address_id is not None:
        update_dict["mail_address_id"] = mail_address_id

    try:
        profile_data = UserUpdateSchema(**update_dict)
    except ValidationError:
        return _error_response("Проверьте корректность заполненных полей")
    except ValueError:
        return _error_response("Проверьте корректность заполненных полей")

    await user_service.update_profile(user, profile_data)
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
    redis_service: RedisService = Depends(get_redis_service)
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

            # Создаем код и сохраняем в Redis
            user_data = {
                "username": username,
                "email": email,
                "telegram_id": str(telegram_id) if telegram_id else "",
                "hashed_password": hashed_password,
            }

            # Генерируем код и сохраняем в Redis
            try:
                code = await redis_service.generate_and_save_verification_code(email, user_data)
                send_verification_email.delay(email, code)
            except VerificationCodeAlreadySent as e:
                return templates.TemplateResponse(
                    request, "user/verify_email.html",
                    {"email": email, "message": str(e)},
                )
            # Отправляем задачу в Celery и показываем пользователю страницу для ввода кода из письма. 
            # send_verification_email.delay(email, code)
            exists = await redis_service.redis_client.exists(f"verify:{email}")
            print("🔑 Ключ сохранён, exists =", exists, "| ключ:", repr(f"verify:{email}"), 
                  f"Код {code}")

            # Показываем страницу ввода кода
            return templates.TemplateResponse(
                request, "user/verify_email.html",
                {"email": email}
              )

    except Exception as e:
        profile_logger.exception("Ошибка при проверке существования пользователя: %s", e)
        return templates.TemplateResponse(
            request, "user/login.html",
            {"error": "Ошибка сервера"}
        )
 

@router.post("/verify", tags=["register"], response_class=HTMLResponse)
async def verify_user(
    request: Request,
    email: str = Form(...), # скрытое поле из прошлой формы
    code: str = Form(...),
    user_service: UserService = Depends(get_user_service),
    redis_service: RedisService = Depends(get_redis_service)
    ):
    """
    Верификация и регистрация пользователя в системе.
    Принимается код, отправиленный на почту пользователя. 
    Достаем данные из Redis.
    Если код введен не верно, отправляем сообщение ошибку кода
    """
    # Достаём данные из Redis по email
    data = await redis_service.get_verification_data(email)
    print("data пользователя", data)
    if not data:
        return templates.TemplateResponse(
            request,
            "user/verify_email.html",
            {"email": email, "message": "Код не найден или истёк. Запросите новый."},
        )

    # Сравниваем код
    if data.get("code") != code:
        print(f"неверный код {data.get("code")}", code)
        return templates.TemplateResponse(
            request,
            "user/verify_email.html",
            {"email": email, "message": "Неверный код"},
        )

    user = UserRegistration(
        username=data["username"],
        email=data["email"],
        telegram_id=data.get("telegram_id") or None,
        password=data["hashed_password"],
        second_password=data["hashed_password"],  # уже проверено на этапе регистрации
    )

    # Сохраняем в бд
    user = await user_service.create_user(user_data=user)  # сохраняем пользователя в базе данных
    if user is None:
        return templates.TemplateResponse(
            request, "user/verify_email.html",
            {"email": email, "message": "Ошибка регистрации. Попробуйте позже."},
        )
    print("Пользователь создан в базе данных", user, user.username, user.email, user.telegram_id)
    profile_logger.info("Зарегистрирован новый пользователь")

    # В этом месте необходимо запустить парсер ЕФРСБ для получения данных о СРО и сохранения их в базу данных.
    # Создаем экземпляр ParserSroDataSaver и передаем его в ParserEFRSB
    
    # start_efrsb_parsing.delay(user_id=user.id, person_name=user.username)  # запускаем Celery задачу для парсинга ЕФРСБ

    # asyncio.run(run_efrsb_parsing(user_id=user.id, person_name=user.username))

    context = {
        "title": "Страница входа",
        "message": "Регистрация прошла успешно",
    }
    return templates.TemplateResponse(request, "user/login.html", context)



