
from fastapi import APIRouter, Depends, Request
from web_app.web_conf import templates

from web_app.utils.dependensy import get_optional_user
from shared.config.db.models import User


router = APIRouter()


@router.get("/", name="help_index")
async def help_index(
    request: Request,
    user: User = Depends(get_optional_user),):
    context = {
        "request": request,
        "title": "Инструкция пользователя",}
    if  user:
        print("пользователь")
        context["user"] = user

    return templates.TemplateResponse(
        request,
        "documentation/help_index.html",
        context
       
    )

@router.get("/about-portal", name="help_about_portal")
async def help_portal(
    request: Request,
    user: User = Depends(get_optional_user),):
    context = {
        "request": request,
        "title": "Руководство пользователя",}
    
    if  user:
        print("пользователь есть")
        context["user"] = user
    print("пользователя нет")
    return templates.TemplateResponse(
        request,
        "documentation/portal.html",
        context=context
    )


@router.get("/debtor-edit", name="help_debtor_edit")
async def help_debtor_edit(
    request: Request,
    user: User = Depends(get_optional_user),):

    context = {
        "request": request,
        "title": "Как редактировать данные должника",}
    
    context["user"] = user

    return templates.TemplateResponse(
        request,
        "documentation/teach_edit_form.html",
        context=context
    )

@router.get("/debtor-faq", name="help_debtor_faq")
async def help_debtor_faq(
    request: Request,
    user: User = Depends(get_optional_user),):
    context = {
        "request": request,
        "title": "Частые вопросы по данным должника",}
    
    context["user"] = user

    return templates.TemplateResponse(
        request,
        "documentation/debtor_faq.html",
        context=context
    )