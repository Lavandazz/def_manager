from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.db.models import Bank


class BankRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, bank_id: int) -> Bank | None:
        return await self.session.get(Bank, bank_id)

    async def get_by_name(self, name: str) -> Bank | None:
        stmt = select(Bank).where(Bank.name == name)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_all(self) -> list[Bank]:
        stmt = select(Bank).order_by(Bank.name)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_bank(self, bank: Bank) -> Bank:
        self.session.add(bank)
        await self.session.flush()   # получить bank.id до commit
        return bank