from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from core.services.user_service import UserService
from app.utils.dependensy import get_optional_user, get_user_service
from app.utils.auth.password_hasher import PasswordHasher
from config.db.models import User
from config.schemas.user_schemas import UserSchema
from config.logger_config import profile_logger

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")



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
        return templates.TemplateResponse(request, "index.html", context={"error": "Пользователь не авторизован"})
    
    return templates.TemplateResponse(request, "/user/profile.html", {
        "user": user
    })

@router.get("/profile/edit", response_class=HTMLResponse)
async def edit_profile_form(request: Request, 
                            user: User = Depends(get_optional_user)):
    
    if not user:
        return templates.TemplateResponse("index.html", {"request": request, "error": "Не авторизован"})
    return templates.TemplateResponse(request, "user/profile_edit.html", {
        "user": user})
        

@router.post("/profile/edit", response_class=HTMLResponse)
async def update_profile(
    request: Request,
    email: str = Form(None),
    telegram_id: int = Form(None),
    password: str = Form(...),
    user: User = Depends(get_optional_user),
    user_service: UserService = Depends(get_user_service)
):
    if not user:
        return templates.TemplateResponse("index.html", {"request": request, "error": "Не авторизован"}, status_code=401)
    
    if not PasswordHasher.verify_password(password, user.hashed_password):
        return templates.TemplateResponse(request, "user/profile_edit.html", {

            "email": email,
            "telegram_id": telegram_id,
            "error": "Неверный пароль"
        }, status_code=400)
    
    # Собираем только переданные поля
    update_dict = {}
    if email is not None:
        update_dict["email"] = email
    if telegram_id is not None:
        update_dict["telegram_id"] = telegram_id if telegram_id != 0 else None
    
    await user_service.update_user(user, UserSchema(**update_dict))
    profile_logger.info("Данные профиля обновлены для user_id=%s", user.id)
    
    return RedirectResponse(url="/user/profile", status_code=303)


