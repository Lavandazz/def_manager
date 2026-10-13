"""
Роут для тестирования подключения тасков.
В проде использоваться не будет
"""

import asyncio

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates

from app.utils.dependensy import get_optional_user
from celery_tasks.task_manager import parsing_task, start_efrsb_parsing

from config.db.models import User
from config.logger_config import fastapi_logger
from parser_app.efrsb_parser import run_efrsb_parsing
from parser_app.kad_parser import run_playwright_parsing


templates = Jinja2Templates(directory="app/templates")
router = APIRouter()



@router.get("/efrsb_{user_id}", tags=["efrsb_parser"])
async def start_efrsb_parsing_from_button(request: Request,
                       user: User = Depends(get_optional_user),
                       ):
    
    if user:
        # Передача задачи в celery
        # task = start_efrsb_parsing.delay(user_id=user.id,
        #                                  person_name=user.username)
        # fastapi_logger.debug(f"Запускаю парсинг {user.username}, task: {task}, {task.id}")

        # Запуск парсинга для отладки без задачи

        await run_efrsb_parsing(user_id=user.id,person_name=user.username)
        # await run_efrsb_parsing(user_id=user.id, person_name="Сатышев Михаил Николаевич")
        fastapi_logger.debug(f"Запускаю парсинг {user.username}")
        
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
        task = parsing_task.delay(case_number=number_case)
        fastapi_logger.debug("Запускаю парсинг по делу %s, task: %s", number_case, task)

        # Запуск парсинга для отладки без задачи
        print(f"Запуск задачи парсинга для дела {number_case}")
        await run_playwright_parsing(number_case)
        
        context = {
            "user": user,
            "message": "Запуск парсинга"}

        return templates.TemplateResponse(request, "index.html", context=context, status_code=201)
    