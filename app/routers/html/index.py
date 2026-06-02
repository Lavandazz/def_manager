from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services.case_service import CaseService
from app.services.user_service import UserService
from app.utils.dependensy import get_case_service, get_user_service, get_verify_user
from config.db.models import User

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")



@router.get("/", response_class=HTMLResponse)
async def main_page(
    request: Request,
    user_service: UserService = Depends(get_user_service),
    case_service: CaseService = Depends(get_case_service)
):
    """
    Главная страница.
    Будет интсрукция и о чем портал. Для отладки оставляются номера cases
    """
    # Для отладки – получаем пользователя по имени или ID
    # Например, захардкодим user_id = 2 
    user_id = 2
    user = await user_service.get_user_by_id(user_id)  # если есть такой метод
    print("Получаю юзера:", user)
    cases = await case_service.get_user_cases(user_id=user_id)
    
    context = {
        "request": request,
        "title": "Главная страница",
        "user": user, 
        "username": user.username if user else "Гость",
        "email": user.email if user else "",
        "telegram_id": user.telegram_id if user else "",
        "cases": cases   # ← передаём дела в шаблон
    }
    return templates.TemplateResponse(request, "index.html", context)
