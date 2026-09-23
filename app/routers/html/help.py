
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", name="help_index")
async def help_index(request: Request):
    return templates.TemplateResponse(
        request,
        "documentation/help_index.html",
        {"title": "Документация портала"},
    )

@router.get("/about-portal", name="help_about_portal")
async def help_portal(request: Request):
    return templates.TemplateResponse(
        request,
        "documentation/portal.html",
        {"title": "О портале"},
    )


@router.get("/debtor-edit", name="help_debtor_edit")
async def help_debtor_edit(request: Request):
    return templates.TemplateResponse(
        request,
        "documentation/teach_edit_form.html",
        {"title": "Как редактировать данные должника"},
    )

@router.get("/debtor-faq", name="help_debtor_faq")
async def help_debtor_faq(request: Request):
    return templates.TemplateResponse(
        request,
        "documentation/debtor_faq.html",
        {"title": "Частые вопросы по данным должника"},
    )