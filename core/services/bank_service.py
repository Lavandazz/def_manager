from config.db.models import Bank
from core.repository.bank_repository import BankRepository


class BankService:
    def __init__(self, repo: BankRepository):
        self.repo = repo

    async def list_banks(self) -> list[Bank]:
        return await self.repo.list_all()

    async def get_bank(self, bank_id: int) -> Bank | None:
        return await self.repo.get_by_id(bank_id)

    async def get_or_create_bank(self, name: str) -> Bank:
        name = (name or "").strip()
        if not name:
            raise ValueError("Название банка обязательно")

        existing = await self.repo.get_by_name(name)
        if existing:
            return existing

        bank = Bank(name=name)
        return await self.repo.create_bank(bank)