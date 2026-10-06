"""
Сервис для создания запросов в банки
"""
from datetime import datetime, date, timedelta
from itertools import groupby



from config.db.models import Account, Case, Debtor
from utils.helper import text_helper

class ContextBuilder:
    def __init__(self, case: Case):
        self.case = case
        self.debtor: Debtor = case.debtor # type: ignore

    def base_context(self) -> dict:
        return self._make_context()

    def _birth_address(self, debtor) -> str:
        return text_helper.get_debtor_address_str(debtor=debtor, birth=True)

    def _residential_address(self, debtor) -> str:
        return text_helper.get_debtor_address_str(debtor=debtor, birth=False)

    def _make_context(self) -> dict:
        """Создание контекста для страницы отображения данных о должнике"""
        reg_address = self._residential_address(self.debtor)  if self.debtor else None
        birth_address = self._birth_address(self.debtor) if self.debtor else None
        today = date.today()
        request_date = today
        date_for = today + timedelta(days=20)

        return {
                "title": f"Данные для генерации — {self.case.number_case}",
                "case": self.case,
                "debtor": self.debtor,
                "reg_address": reg_address,
                "birth_address": birth_address,
                "request_date": request_date,
                "date_for": date_for,
                "bank_name": None,   
            }
    
    def _base_debtor_context(self, region_court: str = "Московской области") -> dict:
        """Общие поля для bank и requests шаблонов."""
        case_date: date = self.case.date_case # type: ignore
        request_date = date(case_date.year - 3, 1, 1)
        date_for = datetime.now().date() + timedelta(days=20)
        decline = text_helper.get_decline_name(self.debtor.name)
        short_name = text_helper.get_short_name(self.debtor.name)

        return {
            "debtor_decline_name": decline[0],
            "debtor_full_name": self.debtor.name,
            "debtor_name": short_name,

            "native": decline[1],
            "insolvent": decline[2],

            "case_date": case_date.strftime("%d.%m.%Y"),
            "case_number": self.case.number_case,

            "debtor_birthday": self.debtor.birthday.strftime("%d.%m.%Y") if self.debtor.birthday else "",
            "debtor_birth_address": text_helper.get_debtor_address_str(self.debtor, birth=True),
            "debtor_snils": text_helper.snils_str(self.debtor.snils) if self.debtor.snils else "",
            "debtor_inn": str(self.debtor.inn) if self.debtor.inn else "",
            "debtor_address": text_helper.get_debtor_address_str(self.debtor, birth=False),

            "request_date": f"01.01.{request_date.year}",
            "date_for": date_for.strftime("%d.%m.%Y"),
            "region_court": region_court,
        }

    def build_requests_context(self, region_court: str = "Московской области") -> dict:
        """Коонтекст для запросов в госорганы"""
        ctx = self._base_debtor_context(region_court)
        ctx.update({
            "fio": text_helper.get_initials(self.debtor.name),
            "year": datetime.now().year,
            "creation_date": datetime.now().strftime("%d.%m.%Y"),
        })
        return ctx


    def build_bank_contexts(self) -> list[dict]:
        """
        Один context на каждый банк должника.
        Счета группируем по bank_id.
        """
        base = self._base_debtor_context()
        short_name = base["debtor_name"]
        # сортировка для groupby
        accounts: list[Account] = sorted(self.debtor.accounts or [], key=lambda a: a.bank_id)
        result = []
        for bank_id, group in groupby(accounts, key=lambda a: a.bank_id):
            accs = list(group)
            bank = accs[0].bank
            ctx = {
                **base,
                "debtor_bank": bank.name,
                "bank_address": text_helper.get_bank_address_str(bank),
                "debtor_accounts": ", ".join(a.number for a in accs),
                "_short_name": short_name,   # служебное — для имени файла
                "_bank_name": bank.name,
            }
            print("данные банка", ctx.get("debtor_accounts"))
            result.append(ctx)
        return result

