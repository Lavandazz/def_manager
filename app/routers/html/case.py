from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette import status

from app.services.case_service import CaseService
from app.services.user_service import UserService
from app.utils.dependensy import get_case_service, get_user_service, get_verify_user
from config.db.models import User

from datetime import datetime
import time


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/{case_id}", response_class=HTMLResponse)
async def case_detail(
    request: Request,
    case_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1),
    case_service: CaseService = Depends(get_case_service)
):
    # Получаем само дело (без документов, или с ними, но мы всё равно их не используем)
    case = await case_service.get_case(case_id=case_id)  # должен возвращать Case по id
    
    # Получаем документы с пагинацией
    documents, total_docs = await case_service.get_case_documents_paginated(case_id, page, size)
    
    total_pages = (total_docs + size - 1) // size if total_docs > 0 else 1
    
    context = {
        "request": request,
        "title": case.number_case,
        "case": case,
        "documents": documents,
        "page": page,
        "size": size,
        "total_pages": total_pages,
        "total_docs": total_docs,
    }
    return templates.TemplateResponse(request, "case/case_detail.html", context)

# @router.get("/", response_class=HTMLResponse)
# async def case_detail(
#     request: Request,
#     case_id: int,
#     page: int =Query(1, ge=1),
#     size: int =Query(10, ge=1),
#     user_service: UserService = Depends(get_user_service),
#     case_service: CaseService = Depends(get_case_service)
# ):
#     """
#     Отображение страницы сданными о деле
#     """
#     case = await case_service.get_case(case_id=case_id)
#     total_docs = len(case.pars_documents)
#     pages = (total_docs + size - 1) // size  # Вычисляем общее количество страниц

#     context = {
#         "request": request,
#         "title": case.number_case,
#         "case": case,
        
#     }

#     return templates.TemplateResponse(request, "case/case_detail.html", context)



async def timer(func):
    async def wrapper(*args, **kwargs):
        start= time.perf_counter()
        result = await func(*args, **kwargs)
        end = time.perf_counter()
        print(f"Время выполнения функции {func.__name__}: {end - start}")
        return result
    return wrapper


async def total_docs_in_case(case):
    return len(case.pars_documents)