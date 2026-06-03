from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services.case_service import CaseService

from app.utils.dependensy import get_case_service, get_optional_user
from config.db.models import User

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


@router.get("/homemage", response_class=HTMLResponse)
async def homepage(
    request: Request,
    user: User = Depends(get_optional_user),
    case_service: CaseService = Depends(get_case_service)
):
    """
    Страница профиля и всех данных зарегитстрированного пользователя """
    cases = await case_service.get_user_cases(user_id=user.id)
    
    context = {
        "request": request,
        "title": "Главная страница",
        "user": user,
        "email": user.email if user else "",
        "telegram_id": user.telegram_id if user else "",
        "cases": cases   # ← передаём дела в шаблон
    }
    return templates.TemplateResponse(request, "index.html", context)
