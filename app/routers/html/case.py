from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services.case_service import CaseService
from app.services.court_service import CourtService
from app.utils.dependensy import get_case_service, get_optional_user, get_court_service
from config.db.models import User


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/courts", response_class=HTMLResponse)
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
    for court in courts:
        print(f"Заседание: {court.date_court} {court.time_court}")
        print(f"Связанные данные дела: {court.case.number_case if court.case else 'Нет данных о деле'}")

    context = {
        "request": request,
        "title": "Календарь судебных заседаний",
        "user": user,
        "courts": courts
    }
    return templates.TemplateResponse(request, "case/court_detail.html", context)


@router.get("/{case_id}", response_class=HTMLResponse)
async def case_detail(
    request: Request,
    case_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1),
    case_service: CaseService = Depends(get_case_service),
    user: User = Depends(get_optional_user),
):
    case = await case_service.get_case(case_id=case_id)  # должен возвращать Case по id
    
    # Получаем документы с пагинацией
    documents, total_docs = await case_service.get_case_documents_paginated(case_id, page, size)
    
    total_pages = (total_docs + size - 1) // size if total_docs > 0 else 1
    
    context = {
        "request": request,
        "user": user,
        "title": case.number_case,
        "case": case,
        "documents": documents,
        "page": page,
        "size": size,
        "total_pages": total_pages,
        "total_docs": total_docs,
    }
    return templates.TemplateResponse(request, "case/case_detail.html", context)
