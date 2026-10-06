
from datetime import date, timedelta
import re

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from jinja2 import UndefinedError
from app.utils.caches_data import get_cases_from_cache
from core.services.case_service import CaseService
from app.utils.dependensy import get_case_service, get_debtor_service, get_document_service, get_optional_user
from celery_tasks.task_manager import parsing_task
from config.db.models import Account, Case, Debtor, User
from core.services.debtor_service import DebtorService
from documents.services.doc_service import OUTPUT_DIR, DocumentService
from documents.utils.context_builder import ContextBuilder
from documents.utils.models import GenerateFormData
from utils.helper import text_helper



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
    total_pages = (total_docs + size - 1) // size if total_docs > 0 else 1

    cached_data = await get_cases_from_cache(user_id=user.id) # получаем cases из кэша

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


@router.post("/{case_id}/delete", tags=["html_case"], response_class=HTMLResponse)
async def delete_case(
    request: Request,
    case_id: int,
    case_service: CaseService = Depends(get_case_service),
    user: User = Depends(get_optional_user),
):
    if not user:
            return templates.TemplateResponse(request, "index.html", 
                                            context={"title": "Главная страница",
                                                    "message": "Необходимо авторизоваться"})
    cached_data = await get_cases_from_cache(user_id=user.id) # получаем cases из кэша
    delete_case = await case_service.delete_case(case_id=case_id)
    
    context = {
            "request": request,
            "user": user,
        }
    if cached_data:
        context["cases"] = cached_data
    if delete_case:
            message = "Дело удалено." \
            "Если Вы удалили дело по ошибке, обратитесь к администратору портала или напишите ваше обращено на электронную почту:" \
            "nepomnu89@ya.ru " \
            "или в telegram:" \
            "@itLavandazz"

            context["message"] = message
    
            
    return templates.TemplateResponse(request, "index.html", context, status_code=200)


@router.get("/generate_documents/{case_id}", tags=["html_docs"], response_class=HTMLResponse)
async def get_generate_documents(
    request: Request,
    case_id: int,
    user: User = Depends(get_optional_user),
    case_service: CaseService = Depends(get_case_service),
):
    """
    Роут отображает данные пользователю, которые попадут в генерацию документов.
    """
    if not user:
        return templates.TemplateResponse(
            request, "index.html",
            context={
                "title": "Главная страница",
                "message": "Для отображения календаря войдите или зарегистрируйтесь",
            },
        )

    case: Case | None = await case_service.get_case_for_documents(case_id)

    if not case or case.id_user != user.id:
        return templates.TemplateResponse(
            request, "index.html",
            context={"message": "Дело не найдено"},
            status_code=404,
        )

    # Достаём должника и связанные данные с помощью метода text_helper
    # context = text_helper.make_context(case)
    ctx = ContextBuilder(case)
    context: dict = ctx.base_context()
    context["user"]=user
    context["template"]= "requests"

    try:
        return templates.TemplateResponse(
            request,
            "documents/generate_form.html",
            context
        )
    except (AttributeError, UndefinedError) as e:
        return templates.TemplateResponse(
            request, "documents/missing_data.html",
            {
                "user": user,
                "title": "Ошибка данных",
                "case_id": case_id,
                "case_number": case.number_case,
                "debtor": case.debtor,
            },
            status_code=500,
        )
    
@router.post("/generate_documents/{case_id}", tags=["html_docs"], response_class=HTMLResponse)
async def generate_documents(
    request: Request,
    case_id: int,
    # form: GenerateFormData = Form(),
    # template: str = Form(...),          # "requests" | "bank"
    region_court: str = Form("Московской области"),
    user: User = Depends(get_optional_user),
    case_service: CaseService = Depends(get_case_service),
    doc_service: DocumentService = Depends(get_document_service),
):
    print("генерация документа")
    if not user:
        return templates.TemplateResponse(
            request, "index.html",
            context={"message": "Необходимо авторизоваться"},
            status_code=401,
        )

    # Собираем контекст
    case: Case | None = await case_service.get_case_for_documents(case_id)
    
    if not case or case.id_user != user.id:
        return templates.TemplateResponse(
            request, "index.html",
            context={"message": "Дело не найдено"},
            status_code=404,
        )
    
    context_builder = ContextBuilder(case)
    context: dict = context_builder.build_requests_context()
    context_bank = context_builder.build_bank_contexts()
    context["user"]=user
    context["template"]= "requests"
    short_name = text_helper.get_short_name(context.get("debtor_full_name")) # создаем наименование файла
    try:
        try:
            # Генерируется запрос в госорганы
            paths_requests = await doc_service.generate_request_doc(
                    context=context,
                    short_name=short_name,
                )
        except Exception as e:
                print("ошибка запросов в госорганы", e)
        try:
            # Генерируется запрос в банки
            paths_banks = await doc_service.generate_banks_docs(
                contexts=context_bank, 
                short_name=short_name)

        except Exception as e:
            print("ошибка запросов в банк", e)

    except Exception as e:
        print("ошибка запросы сгенерирвоаны", e)
        return templates.TemplateResponse(
            request, "documents/generate_form.html",
            {"user": user,
            "title": f"Генерация документов — {case.number_case}",
            "case_id": case_id,
            "case": case,
            "case_number": case.number_case,            
            "debtor": case.debtor, "message": f"Ошибка генерации: {e}"},
            status_code=500,
        )

    return templates.TemplateResponse(
        request,
        "documents/generate_form.html",
        {
            "user": user,
            "title": f"Генерация документов — {case.number_case}",
            "case_id": case_id,
            "case": case,
            "case_number": case.number_case,            
            "debtor": case.debtor,
        }
    )

@router.get("/download/{subdir}/{filename}", tags=["html_docs"])
async def download_document(
    subdir: str,
    filename: str,
    user: User = Depends(get_optional_user),
):
    if not user:
        return HTMLResponse("Необходимо авторизоваться", status_code=401)
    # защита от path traversal
    if ".." in subdir or ".." in filename or "/" in filename:
        return HTMLResponse("Некорректный путь", status_code=400)
    file_path = (OUTPUT_DIR / subdir / filename).resolve()
    if not file_path.is_relative_to(OUTPUT_DIR.resolve()) or not file_path.exists():
        return HTMLResponse("Файл не найден", status_code=404)
    return FileResponse(
        file_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=filename,
    )