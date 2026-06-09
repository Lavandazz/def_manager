from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates

from app.services.case_service import CaseService
from app.utils.dependensy import get_case_service, get_optional_user
from config.db.models import User
from parser.parser_plw import run_playwright_parsing


templates = Jinja2Templates(directory="app/templates")
router = APIRouter()


@router.get("/{case_id}", tags=["html_parser"])
async def start_parser(request: Request,
                       case_id: int,
                       case_service: CaseService = Depends(get_case_service),
                       user: User = Depends(get_optional_user)):
    
    print("Роут парсинга")
    if user:
        case = await case_service.get_case(case_id=case_id)
        
        parsing = await run_playwright_parsing(case_number=case.number_case)
        print("Запускаю парсинг по делу %s", case.number_case)
        if parsing:
            context = {"agree_message": "Запуск парсинга"}

            return templates.TemplateResponse(request, "index.html", context=context, status_code=201)
