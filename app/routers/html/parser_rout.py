"""
Роут для тестирования подключения тасков.
В проде использоваться не будет
"""

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates

from app.utils.dependensy import get_optional_user
from celery_app.task_manager import parsing_task

from config.db.models import User
from config.logger_config import fastapi_logger


templates = Jinja2Templates(directory="app/templates")
router = APIRouter()


@router.get("/{number_case:path}", tags=["html_parser"])
async def start_parser(request: Request,
                       number_case: str,
                       user: User = Depends(get_optional_user),
                       ):
    
    if user:
        task = parsing_task.delay(case_number=number_case)

        fastapi_logger.debug("Запускаю парсинг по делу %s, task: %s", number_case, task)
        context = {"agree_message": "Запуск парсинга"}

        return templates.TemplateResponse(request, "index.html", context=context, status_code=201)

