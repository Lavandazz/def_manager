"""
Сервис для создания запросов по имуществу должника.
- МЧС
- ПФР
- Росгвадрия
- ЗАГС
- Гостехнадзор
- ГИБДД
"""
from datetime import datetime, date, timedelta

from schemas.case_schemas import Case
from schemas.debtor import Debtor
from mock_data.debtor import person_data
from mock_data.case import case as case_data
from utils.context_utils import text_helper

debtor = Debtor.model_validate(person_data)
short_name = text_helper.get_short_name(debtor.name)
case = Case.model_validate(case_data)

request_date = date(case.date.year - 3, 1, 1)
current_date = datetime.now().date()
date_for = current_date + timedelta(days=20)
decline_name = text_helper.get_decline_name(debtor.name)


context = {
    "fio":text_helper.get_initials(debtor.name),
    "year": current_date.year,
    "creation_date": current_date.strftime("%d.%m.%Y"),
    "debtor_decline_name" : decline_name[0],
    "debtor_full_name": debtor.name,
    "debtor_name": short_name,
    "native": decline_name[1],
    
    "insolvent": decline_name[2],

    "case_date": case.date.strftime("%d.%m.%Y"),
    "case_number": case.number,

    "debtor_birthday": debtor.birthday.strftime("%d.%m.%Y"),
    "debtor_birth_address": text_helper.get_debtor_address_str(debtor, birth=True),
    "debtor_snils": text_helper.snils_str(debtor.snils),
    "debtor_inn": debtor.inn,
    "debtor_address": text_helper.get_debtor_address_str(debtor, birth=False),

    "request_date": f"01.01.{request_date.year}",
    "date_for": date_for.strftime("%d.%m.%Y"),

    "region_court": "Московской области"
    }