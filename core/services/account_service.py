from config.db.models import Account
from core.repository.account_repository import AccountRepository
from core.services.bank_service import BankService


class AccountService:
    def __init__(self, repo: AccountRepository, bank_service: BankService):
        self.repo = repo
        self.bank_service = bank_service

    async def list_by_debtor(self, debtor_id: int) -> list[Account]:
        return await self.repo.list_by_debtor(debtor_id)

    async def sync_accounts( self, debtor_id: int, accounts_data: list[dict] ) -> list[Account]:
        """
        Синхронизирует счета должника с данными из формы.

        accounts_data — список словарей вида:
            {"id": int | None, "number": str, "bank_id": int | None}
            {"number": str, "bank_id": int, "bank_name": str}  # для нового банка

        Логика:
          - есть id и есть number/bank  → обновить
          - нет id и есть number/bank   → создать
          - есть id в БД, но нет в форме → удалить
        """
        # Проверка что есть в БД
        existing = await self.repo.list_by_debtor(debtor_id)
        existing_by_id = {acc.id: acc for acc in existing}

        #  id, которые пришли из формы (существующие)
        incoming_ids: set[int] = set()

        for item in accounts_data:
            number = (item.get("number") or "").strip()
            bank_id = item.get("bank_id")
            bank_name = (item.get("bank_name") or "").strip()

            # полностью пустая строка — пропускаем
            if not number and not bank_id and not bank_name:
                continue

            # новый банк по имени + адресу
            if not bank_id and bank_name:
                bank = await self.bank_service.get_or_create_bank(
                    name=bank_name,
                    mail_index=item.get("bank_mail_index"),
                    city=item.get("bank_city"),
                    region_name=item.get("bank_region_name"),
                    street=item.get("bank_street"),
                    house=item.get("bank_house"),
                    building=item.get("bank_building"),
                )
                bank_id = bank.id

            account_id = item.get("id")

            if account_id and account_id in existing_by_id:
                account = existing_by_id[account_id]
                # пустые строки не перезаписываем
                final_number = number or account.number
                final_bank_id = bank_id or account.bank_id

                if not final_number or not final_bank_id:
                    continue

                account.number = final_number
                account.bank_id = final_bank_id
                incoming_ids.add(account_id)
            else:
                # новый счёт — оба поля обязательны
                if not number or not bank_id:
                    continue

                account = Account(
                    debtor_id=debtor_id,
                    number=number,
                    bank_id=bank_id,
                )
                await self.repo.create_account(account)

        #  Удаляем те, что были в БД, но не пришли из формы
        for acc_id, account in existing_by_id.items():
            if acc_id not in incoming_ids:
                await self.repo.delete_account(account)

        #  Возвращаем актуальный список
        return await self.repo.list_by_debtor(debtor_id)