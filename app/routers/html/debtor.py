
from datetime import date, datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.utils.caches_data import get_cases_from_cache
from config.schemas.case_schemas import CaseSchema, DebtorSchema
from core.services.address_service import ResidentialAddressService
from core.services.case_service import CaseService
from app.utils.dependensy import get_case_service, get_debtor_service, get_optional_user, get_region_service, get_residential_address_service
from celery_tasks.task_manager import parsing_task
from config.db.models import Case, Debtor, DebtorType, User
from core.services.debtor_service import DebtorService
from core.services.region_service import RegionService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/choice_debtor", tags=["html_debtor"], response_class=HTMLResponse)
async def get_choice_debtor(        
    request: Request,
    user: User = Depends(get_optional_user),
    case_service: CaseService = Depends(get_case_service)
    ):
    """
    Отображение страницы для введения данных для физ должника
    """
    if not user:
        return templates.TemplateResponse(request, "index.html", 
                                          context={"title": "Главная страница",
                                                   "message": "Необходимо авторизоваться"})
    
    cached_data = get_cases_from_cache(user_id=user.id) # получаем cases из кэша
    cases_physical = await case_service.get_user_cases_by_type(user_id=user.id, debtor_type="PHYSICAL")
    context = {
        "request": request,
        "user": user,
        "title": "Выберите должника для редактирования данных",
        "cases_physical": cases_physical
    }

    if cached_data:
        context["cases"] = cached_data
    print("~~~~", cases_physical)
    

    return templates.TemplateResponse(
        request, 
        "debtor/choice_edit_debtor.html", 
        context
        )


def _debtor_to_form(d) -> dict:
    return {
        "debtor_type": d.debtor_type.value if d.debtor_type else "",
        "name": d.name or "",
        "inn": str(d.inn) if d.inn else "",
        "snils": str(d.snils) if d.snils else "",
        "birthday": d.birthday.isoformat() if d.birthday else "",
        "birth_region": str(d.birth_region) if d.birth_region else "",
        "residential_address": str(d.residential_address) if d.residential_address else "",
    }

@router.get("/{debtor_id}/edit", response_class=HTMLResponse, name="debtor_edit")
async def debtor_edit(
    request: Request,
    debtor_id: int,
    user: User = Depends(get_optional_user),
    debtor_service: DebtorService = Depends(get_debtor_service),
    region_service: RegionService = Depends(get_region_service),
    residential_service: ResidentialAddressService = Depends(get_residential_address_service)
):
    """Отправление формы для редактирования должника"""
    if not user:
        return templates.TemplateResponse(request, "index.html", 
                                          context={"title": "Главная страница",
                                                   "message": "Необходимо авторизоваться"})
    cached_cases = get_cases_from_cache(user.id) 
    cached_debtor = None
    if cached_cases:
        for c in cached_cases:
            if c.get("debtor_id") == debtor_id:
                cached_debtor = c
                break


    debtor_data = await debtor_service.get_debtor(user.id, debtor_id)
    print("debtor_data:", debtor_data.debtor.residential_address)   
    if debtor_data is None:
        raise HTTPException(404, "Должник не найден")
    
    regions = await region_service.list_regions()
    residential_addresses = await residential_service.list_addresses()

    context = {
        "request": request,
        "user": user,
        "title": f"Редактирование должника",
        "debtor_data": debtor_data,
        "accounts": debtor_data.accounts,
        "regions": regions,
        "residential_addresses": residential_addresses,
        "cached_debtor": cached_debtor,
        "form": _debtor_to_form(debtor_data.debtor),
    }
    return templates.TemplateResponse(
        request,
        "debtor/debtor_edit.html",
        context
    )

def to_int_or_none(v: str) -> int | None:
    v = (v or "").strip()
    return int(v) if v else None

def to_date_or_none(v: str) -> date | None:
    v = (v or "").strip()
    return datetime.strptime(v, "%Y-%m-%d").date() if v else None


@router.post("/debtors/{debtor_id}/edit", name="debtor_edit_post")
async def debtor_edit_post(
    request: Request,
    debtor_id: int,
    debtor_type: str = Form(...),
    name: str = Form(...),
    inn: str = Form(""),
    snils: str = Form(""),
    birthday: str = Form(""),

    birth_region_mode: str = Form("existing"),
    birth_region_id: str = Form(""),
    new_birth_region_name: str = Form(""),
    new_birth_region_city: str = Form(""),

    residential_address_mode: str = Form("existing"),
    residential_address_id: str = Form(""),
    new_ra_region_name: str = Form(""),
    new_ra_city: str = Form(""),
    new_ra_street: str = Form(""),
    new_ra_house: str = Form(""),
    new_ra_building: str = Form(""),
    new_ra_flat: str = Form(""),
    user: User = Depends(get_optional_user),
    debtor_service: DebtorService = Depends(get_debtor_service),
):
    if not user:
        return RedirectResponse(request.url_for("index"), status_code=303)

    #  Достаём поля для банков через getlist ──
    form = await request.form()

    account_ids        = form.getlist("account_id[]")
    account_numbers    = form.getlist("account_number[]")
    account_bank_modes = form.getlist("account_bank_mode[]")       # "existing" | "new"
    account_bank_ids   = form.getlist("account_bank_id[]")         # id существующего банка

    new_bank_names     = form.getlist("new_bank_name[]")
    new_bank_indexes   = form.getlist("new_bank_mail_index[]")
    new_bank_regions   = form.getlist("new_bank_region_name[]")
    new_bank_cities    = form.getlist("new_bank_city[]")
    new_bank_streets   = form.getlist("new_bank_street[]")
    new_bank_houses    = form.getlist("new_bank_house[]")
    new_bank_buildings = form.getlist("new_bank_building[]")

    # 1. Собираем словарь — уже с нормальными типами
    data = {
        # скалярные поля
        "debtor_type": DebtorType(debtor_type),
        "name": name.strip(),
        "inn": to_int_or_none(inn),
        "snils": to_int_or_none(snils),
        "birthday": to_date_or_none(birthday),

        # регион рождения
        "birth_region_mode": birth_region_mode,
        "birth_region_id": to_int_or_none(birth_region_id),
        "new_birth_region_name": new_birth_region_name.strip() or None,
        "new_birth_region_city": new_birth_region_city.strip() or None,

        # адрес прописки
        "residential_address_mode": residential_address_mode,
        "residential_address_id": to_int_or_none(residential_address_id),
        "new_ra_region_name": new_ra_region_name.strip() or None,
        "new_ra_city": new_ra_city.strip() or None,
        "new_ra_street": new_ra_street.strip() or None,
        "new_ra_house": new_ra_house.strip() or None,
        "new_ra_building": new_ra_building.strip() or None,
        "new_ra_flat": new_ra_flat.strip() or None,
    }
    print("полученный данные из редактирования:", data)
    
    # 2. Отдаём в сервис
    await debtor_service.update_debtor(user.id, debtor_id, data)

    # 3. Редирект обратно на форму
    return RedirectResponse(
        url=request.url_for("debtor_edit", debtor_id=debtor_id),
        status_code=303,
    )