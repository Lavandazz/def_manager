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

            # если банк задан именем — создаём/находим
            if not bank_id and bank_name:
                bank = await self.bank_service.get_or_create_bank(bank_name)
                bank_id = bank.id

            if not number or not bank_id:
                # неполная строка — пропускаем (или бросить ошибку валидации)
                continue

            account_id = item.get("id")

            if account_id and account_id in existing_by_id:
                # обновляем
                account = existing_by_id[account_id]
                account.number = number
                account.bank_id = bank_id
                incoming_ids.add(account_id)
            else:
                # создаём
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