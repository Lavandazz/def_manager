import re

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services.case_service import CaseService
from app.utils.dependensy import get_case_service, get_optional_user
from celery_app.task_manager import parsing_task
from config.db.models import Case, User


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# проверка номера дела
PATTERN_CASE = re.compile(r'^[A-ZА-Я]\d{2}-\d{5}/\d{4}$', re.IGNORECASE)


@router.get("/create", tags=["html_case"], response_class=HTMLResponse)
async def add_case_form(
        request: Request,
        user: User = Depends(get_optional_user),
    ):
    """
    Отображение страницы для введения номера дела 
    """
    if user:
        return templates.TemplateResponse(request, 
                                          "case/add_case.html", 
                                          {"title": "Создание дела", "user": user})
    return templates.TemplateResponse(request, "index.html", context={"title": "Главная страница"})


@router.post("", tags=["html_case"], response_class=HTMLResponse)
async def add_case(
    request: Request,
    number_case: str = Form(),
    debtor: str = Form(),
    user: User = Depends(get_optional_user),
    case_service: CaseService = Depends(get_case_service)
    ):
    """
    Отображение страницы для введения номера дела 
    """
    ###
    ### Переделать форму через пайдантик с валидацией номера дела
    
    print("Полученные данные: number_case=%s, debtor=%s", number_case, debtor)

    if not user:
        return templates.TemplateResponse("index.html", {"request": request, "error": "Не авторизован"}, status_code=401)
    
    if not PATTERN_CASE.match(number_case.strip()) or not number_case or not isinstance(number_case, str):
        context = {
            "title": "Создание дела",
            "user": user,
            "number_case": number_case,
            "debtor": debtor,
            "error": "Некорректный формат номера дела. Ожидается, например: А40-12345/2024"
        }
        return templates.TemplateResponse(
            request,
            "case/add_case.html",
            context,
            status_code=400
        )

    new_case = Case(
    number_case=number_case,
    debtor=debtor,
    id_user=user.id
    )
    case = await case_service.add_case(new_case)
    # Создается таска для парсинга дела

    task = parsing_task.delay(case_number=number_case)
    print("Дело успешно добавлено %s", number_case, case)
    print("Запускаю парсинг по делу %s", number_case, task)

    context = {"agree_message": "Дело успешно добавлено"}
    return templates.TemplateResponse(request, "index.html", context, status_code=201)


@router.get("/{case_id}", tags=["html_case"], response_class=HTMLResponse)
async def case_detail(
    request: Request,
    case_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1),
    case_service: CaseService = Depends(get_case_service),
    user: User = Depends(get_optional_user),
):
    # fastapi_logger.warning(f"Request from {request.client.host}, UA: {request.headers.get('user-agent')}")
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


