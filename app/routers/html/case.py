import json
import re

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.utils.caches_data import get_cases_from_cache
from config.redis_config import redis_client
from config.schemas import documents_schema
from core.services.case_service import CaseService
from app.utils.dependensy import get_case_service, get_debtor_service, get_optional_user
from celery_tasks.task_manager import parsing_task
from config.db.models import Case, Debtor, User
from core.services.debtor_service import DebtorService


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
    debtor_type: str = Form(),
    debtor_name: str = Form(),
    user: User = Depends(get_optional_user),
    case_service: CaseService = Depends(get_case_service),
    debtor_service: DebtorService = Depends(get_debtor_service)
    ):
    """
    Создание номера дела 
    """
    ###
    ### Переделать форму через пайдантик с валидацией номера дела

    if not user:
        return templates.TemplateResponse("index.html", {"request": request, "error": "Не авторизован"}, status_code=401)
    
    if not PATTERN_CASE.match(number_case.strip()) or not number_case or not isinstance(number_case, str):
        context = {
            "title": "Создание дела",
            "user": user,
            "number_case": number_case,
            "debtor": debtor_name,
            "message":"Некорректный формат номера дела. Ожидается, например: А40-12345/2024"
            }
        return templates.TemplateResponse(
            request,
            "case/add_case.html",
            context,
            status_code=400
        )
    new_debtor = Debtor(name=debtor_name, debtor_type=debtor_type)
    debtor = await debtor_service.add_debtor(new_debtor)

    
    new_case = Case(
    number_case=number_case,
    debtor_id=debtor.id,
    id_user=user.id
    )
    case = await case_service.add_case(new_case)
    # Создается таска для парсинга дела

    task = parsing_task.delay(case_number=number_case)

    print("Дело успешно добавлено","Запускаю парсинг по делу %s", number_case, task)

    context = {"message":"Дело успешно добавлено",
               "user": user}

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
    if not user:
        return templates.TemplateResponse(request, "index.html", 
                                          context={"title": "Главная страница",
                                                   "message": "Необходимо авторизоваться"})
    case = await case_service.get_case(case_id=case_id)  # возврат Case по id
    
    # Получаем документы с пагинацией
    documents, total_docs = await case_service.get_case_documents_paginated(case_id, page, size)
    for document in documents:
        print(document.date if document.id == 12 else type(document.date))
    total_pages = (total_docs + size - 1) // size if total_docs > 0 else 1

    cached_data = get_cases_from_cache(user_id=user.id) # получаем cases из кэша

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
    if cached_data:
        context["cases"] = cached_data

    return templates.TemplateResponse(request, "case/case_detail.html", context)


