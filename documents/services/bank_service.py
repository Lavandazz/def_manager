"""
Сервис для создания запросов в банки
"""
from datetime import datetime, date, timedelta

from schemas.bank_schemas import Bank
from schemas.case_schemas import Case
from schemas.debtor import Debtor
from mock_data.debtor import person_data
from mock_data.bank import bank_data
from mock_data.case import case as case_data
from utils.context_utils import text_helper

debtor = Debtor.model_validate(person_data)
short_name = text_helper.get_short_name(debtor.name)
bank = Bank.model_validate(bank_data)
bank_name = bank.name
case = Case.model_validate(case_data)

request_date = date(case.date.year - 3, 1, 1)
date_for = datetime.now().date() + timedelta(days=20)

decline_name = text_helper.get_decline_name(debtor.name)

context = {"debtor_decline_name" : decline_name[0],
           "debtor_full_name": debtor.name,
           "debtor_name": short_name,
           "native": decline_name[1],
           "debtor_bank": bank.name,
           "bank_address": text_helper.get_bank_address_str(bank),

           "case_date": case.date.strftime("%d.%m.%Y"),
           "case_number": case.number,

           "debtor_birthday": debtor.birthday.strftime("%d.%m.%Y"),
           "debtor_birth_address": text_helper.get_debtor_address_str(debtor, birth=True),
           "debtor_snils": text_helper.snils_str(debtor.snils),
           "debtor_inn": debtor.inn,
           "debtor_address": text_helper.get_debtor_address_str(debtor, birth=False),

           "request_date": f"01.01.{request_date.year}",
           "date_for": date_for.strftime("%d.%m.%Y"),
           "debtor_accounts": bank.accounts,
           "region_court": "Московской области"
            }