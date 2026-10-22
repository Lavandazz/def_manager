"""
Роут для тестирования подключения тасков.
В проде использоваться не будет
"""

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, Request

from web_app.web_conf import templates

from web_app.utils.dependensy import get_optional_user
from celery_tasks.task_manager import parsing_task, start_efrsb_parsing

from shared.config.tasks_config import celery_app
from shared.config.db.models import User
from shared.config.logger_config import fastapi_logger
from parser_app.efrsb_parser import run_efrsb_parsing
from parser_app.kad_parser import run_playwright_parsing
from shared.utils.exceptions import AccessForbidden


router = APIRouter()


@router.get("/efrsb_{user_id}", tags=["efrsb_parser"])
async def start_efrsb_parsing_from_button(request: Request,
                       user: User = Depends(get_optional_user),
                       ):
    
    if user:
        # Передача задачи в celery
        task = start_efrsb_parsing.delay(user_id=user.id,
                                         person_name=user.username)
        fastapi_logger.debug(f"Запускаю парсинг {user.username}, task: {task}, {task.id}")
        task_result = AsyncResult(task.id, app=celery_app)
        # Запуск парсинга для отладки без задачи
        # fastapi_logger.debug(f"===== Пользователь {user.username} запускает задачу celery")
        # await run_efrsb_parsing(user_id=user.id,person_name=user.username)
        
        if task_result.state == 'FAILURE':
            # Извлекаем исключение, которое сохранил Celery
            exc = task_result.result
            if isinstance(exc, AccessForbidden):
                # Возвращаем понятный клиенту ответ
                print(f"Доступ запрещён для пользователя {user.username}: {exc}")
                raise HTTPException(
                    status_code=403,
                    detail=f"Доступ запрещён: {str(exc)}"
                )
            else:
                print(f"Внутренняя ошибка парсера")
                raise HTTPException(
                    status_code=500,
                    detail=f"Внутренняя ошибка парсера: {str(exc)}"
                )
        
        context = {
            "user": user,
            "message": "Запуск парсинга"}

        return templates.TemplateResponse(request, "index.html", context=context, status_code=201)



@router.get("/{number_case:path}", tags=["html_parser"])
async def start_parser(request: Request,
                       number_case: str,
                       user: User = Depends(get_optional_user),
                       ):
    
    if user:
        # Передача задачи в celery
        # task = parsing_task.delay(case_number=number_case)
        # fastapi_logger.debug(f"Запускаю парсинг по делу {number_case}, task: {task}")

        # Запуск парсинга для отладки без задачи
        print(f"Запуск парсинга для отладки без задачи {number_case}")
        await run_playwright_parsing(number_case)
        
        context = {
            "user": user,
            "message": "Запуск парсинга"}

        return templates.TemplateResponse(request, "index.html", context=context, status_code=201)
    