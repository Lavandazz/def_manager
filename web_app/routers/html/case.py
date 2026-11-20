
import asyncio
import re

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from jinja2 import UndefinedError
from shared.core.services.user_service import UserService
from web_app.web_conf import templates
from web_app.utils.caches_data import get_cases_from_cache
from shared.core.services.case_service import CaseService
from web_app.utils.dependensy import get_case_service, get_debtor_service, get_document_service, get_optional_user, get_user_service
from shared.celery_tasks.task_manager import parsing_task
from shared.config.db.models import Account, Case, Debtor, User, DebtorType
from shared.core.services.debtor_service import DebtorService
from shared.documents.services.doc_service import OUTPUT_DIR, DocumentService
from shared.documents.utils.context_builder import ContextBuilder
from shared.utils.document_text_helper import document_helper
from shared.config.logger_config import fastapi_logger
from shared.utils.exceptions import AccessForbidden, DocumentsDirNotFound

router = APIRouter()


# проверка номера дела
PATTERN_CASE = re.compile(r'^[A-ZА-Я]\d{2}-\d{5,6}/\d{4}$', re.IGNORECASE)


@router.get("/create", tags=["html_case"], response_class=HTMLResponse)
async def add_case_form(
        request: Request,
        user: User = Depends(get_optional_user),
    ):
    """
    Отображение страницы для введения номера дела 
    """
    if not user:
        return templates.TemplateResponse(request, "index.html", context={"title": "Главная страница"})
    context = {
        "title": "Создание дела",
        "user": user
    }
    cached_data = await get_cases_from_cache(user_id=user.id) # получаем cases из кэша
    if cached_data:
        context["cases"] = cached_data
    return templates.TemplateResponse(request, 
                                        "case/add_case.html", 
                                        context=context)


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
        return templates.TemplateResponse(
            request, "index.html",
            {"error": "Не авторизован"},
            status_code=401,
        )
    
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
    fastapi_logger.info(f"Добавлено новый должник {debtor}")
    
    new_case = Case(
    number_case=number_case,
    debtor_id=debtor.id,
    id_user=user.id
    )
    case = await case_service.add_case(new_case)
    
    # Создается таска для парсинга дела
    task = parsing_task.delay(case_number=number_case)
    fastapi_logger.info(f"Дело - {number_case} успешно добавлено, таска парсинга дела - {task} ")

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
    """
    Отображение дела с полученными из судов документами.
    Возможность перехода в генерацию запросов и редактирование данных должника
    """
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
    # Получаем тип должника, если юр.лицо, то кнопку генерации доков не отображаем
    debtor_type = "ph" if case.debtor.debtor_type == DebtorType.PHYSICAL else None
 
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
        "debtor_type": debtor_type
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
    """
    Роут для мягкого удаления дела.
    Если дело не принадледит пользователю, будет сгенерированно сообщение об этом
    """
    if not user:
        return templates.TemplateResponse(
            request, "index.html",
            {"title": "Главная страница", "message": "Необходимо авторизоваться"},
            status_code=401,
        )
    status_code = 200
    message: str | None = None
    cached_data = await get_cases_from_cache(user_id=user.id) # получаем cases из кэша
    try:
        delete = await case_service.delete_case(user_id=user.id, case_id=case_id)
        if delete:
            message = "Дело удалено." \
                "Если Вы удалили дело по ошибке, обратитесь к администратору портала или напишите ваше обращено на электронную почту:" \
                "nepomnu89@ya.ru " \
                "или в telegram:" \
                "@itLavandazz"
        else:
            status_code = 409
            message = "Дело уже удалено или не найдено"

    except AccessForbidden:
        message = "Ошибка доступа"
        status_code = 403

    context = {
            "request": request,
            "user": user,
        }
    
    if cached_data:
        context["cases"] = cached_data

    context["message"] = message
            
    return templates.TemplateResponse(request, "index.html", context=context, status_code=status_code)


@router.get("/generate_documents/{case_id}", tags=["html_docs"], response_class=HTMLResponse)
async def get_generate_documents(
    request: Request,
    case_id: int,
    user: User = Depends(get_optional_user),
    case_service: CaseService = Depends(get_case_service),
):
    """
    Роут отображает данные пользователю, которые попадут в генерацию документов.
    В отображенной странице имеются кнопки для запросов в госорганы/банки, 
    редактирование данные должника и скачивание готовых файлов
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
    ctx = ContextBuilder(case=case, user=user)
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
    template: str = Form(...),          # "requests" | "bank"
    region_court: str = Form("Московской области"),
    user: User = Depends(get_optional_user),
    case_service: CaseService = Depends(get_case_service),
    doc_service: DocumentService = Depends(get_document_service),
    user_service: UserService = Depends(get_user_service)
):
    """
    POST роут для генерации документов.
    При нажатии на кнопку Запросы в госорганы/запросы в банки, отправляется POST на генерацию word документов.
    """
    from shared.utils.document_text_helper import document_helper
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
    user_data: User = await user_service.get_user_profile(user_id=user.id) # явно загружаем данные пользователя через joinedload
    context_builder = ContextBuilder(case=case, user=user_data) # type: ignore из-за  user_data: User | None, выше проверка на пользователя была
    context: dict = context_builder.build_requests_context()
    context_bank = context_builder.build_bank_contexts()
    context["template"]= "requests"
    short_name = document_helper.get_short_name(context.get("debtor_full_name")) # создаем наименование файла
    
    template = (template or "requests").lower()
    file_path = ""
    try:
        if template == "requests":
            await doc_service.generate_request_doc(user_id=user.id, context=context, short_name=short_name)
        elif template == "bank":
            await doc_service.generate_banks_docs(user_id=user.id, contexts=context_bank, short_name=short_name)
        elif template == "both":
            await doc_service.generate_request_doc(user_id=user.id, context=context, short_name=short_name)
            await doc_service.generate_banks_docs(user_id=user.id, contexts=context_bank, short_name=short_name)
        else:
            raise ValueError(f"Неизвестный тип шаблона: {template}")
        
    except Exception as e:
        fastapi_logger.error(f"Ошибка генерации запросов {template}: {e}")
        return templates.TemplateResponse(
            request, "documents/generate_form.html",
            {"user": user,
            "title": f"Генерация документов — {case.number_case}",
            "template": template,   
            "case_id": case_id,
            "case": case,
            "case_number": case.number_case,            
            "debtor": case.debtor, 
            "message": f"Ошибка генерации: {e}"},
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
            "message": f"Документы успешно сгенерированы. Можете скачать по кнопке ниже.",
        }
    )

@router.get("/download/{debtor_id}")
async def download_document(
    request: Request, 
    debtor_id: int,
    user: User = Depends(get_optional_user),
    debtor_service: DebtorService = Depends(get_debtor_service),
    doc_service: DocumentService = Depends(get_document_service),
):
    from urllib.parse import quote
    if not user:
        return HTMLResponse("Необходимо авторизоваться", status_code=401)

    # Сверка должника с пользователем
    debtor = await debtor_service.get_short_debtor(user_id=user.id, debtor_id=debtor_id)

    if debtor is None:
        raise HTTPException(404, "Должник не найден")
    short_name = document_helper.get_short_name(debtor.name) # получаем ФИО Иванов И.И.

    try:
        dir_path = await doc_service.get_documents_path(user.id, short_name)

    except DocumentsDirNotFound as e:
        fastapi_logger.warning(f"Папки с документами для {short_name} не существует")
        raise HTTPException(404, "Сначала сгенерируйте документы")

    # Сбор zip (в отдельном потоке - блокирующий I/O)
    buffer = await asyncio.to_thread(doc_service.zip_folder, dir_path)
    zip_name = f"{short_name}.zip"
    
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={
            # filename* с UTF-8 — кириллица
            "Content-Disposition": (
                f"attachment; filename=\"documents.zip\"; " # attachment — это команда браузеру для скачивания файлов.
                f"filename*=UTF-8''{quote(zip_name)}"
            ),
        },
    )
        