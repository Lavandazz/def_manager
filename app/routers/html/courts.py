from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from core.services.court_service import CourtService
from app.utils.dependensy import get_court_service, get_optional_user
from config.db.models import User

router = APIRouter()
templates = Jinja2Templates("app/templates")


@router.get("/", tags=["html_case"], response_class=HTMLResponse)
async def get_courts(
    request: Request,
    user: User = Depends(get_optional_user),
    court_service: CourtService = Depends(get_court_service)
):
    """
    Получение всех судебных заседаний для текущего пользователя и отображение их на странице."""
    if not user:
        return templates.TemplateResponse(request, "index.html", context={"title": "Главная страница"})
    
    courts = await court_service.get_courts(user_id=user.id)

    context = {
        "request": request,
        "title": "Календарь судебных заседаний",
        "user": user,
        "courts": courts
    }
    return templates.TemplateResponse(request, "case/court_detail.html", context)
