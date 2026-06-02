from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.services.case_service import CaseService
from app.services.user_service import UserService
from app.utils.auth.auth_token import AuthTokenService
from app.utils.auth.password_hasher import PasswordHasher
from app.utils.dependensy import get_case_service, get_user_service, get_optional_user
from config.db.models import User
from config.schemas.token_schemas import AuthTokenSchema


router = APIRouter()

templates = Jinja2Templates(directory="app/templates")



@router.get("/", response_class=HTMLResponse)
async def main_page(
    request: Request,
    user: User = Depends(get_optional_user),
    case_service: CaseService = Depends(get_case_service)
):
    """
    Главная страница.
    Будет интсрукция и о чем портал. Для отладки оставляются номера cases
    """
    context = {
        "request": request,
        "title": "Главная страница",}
    
    if not user:
        return templates.TemplateResponse(request, "layout.html", context)
    
    cases = await case_service.get_user_cases(user_id=user.id)
    context["cases"] = cases
    context["user"] = user

    return templates.TemplateResponse(request, "layout.html", context)



@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    Страница логина. Пока просто шаблон, без логики.
    """
    context = {
        "request": request,
        "title": "Страница входа"
    }
    return templates.TemplateResponse(request, "user/login.html", context)


@router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    telegram_id: str = Form(None),   
    email: str = Form(None),        
    password: str = Form(...), 
    user_service: UserService = Depends(get_user_service)
):
    # Проверяем пользователя (та же логика, что в API /login)

    if not telegram_id and not email:
        return templates.TemplateResponse(
            request, "user/login.html",
            {"error": "Введите Telegram ID или Email"}
        )

    existing_user = await user_service.get_user(email=email, telegram_id=telegram_id)

    if not existing_user or not PasswordHasher.verify_password(password, existing_user.hashed_password):

        return templates.TemplateResponse(
            request, "user/login.html",
            {"error": "Неверный email или пароль"}
        )
    
    # Создаём токен (используем AuthTokenService)
    auth = AuthTokenService()
    token = auth.create_token(data=AuthTokenSchema(id=existing_user.id, email=existing_user.email, telegram_id=existing_user.telegram_id))

    # Перенаправляем на главную и устанавливаем cookie
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,   # Защита от XSS
        max_age=3600,    # Время жизни в секундах
        # secure=True,   # Только для HTTPS, включить на проде
        # samesite="lax"
    )
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    return response