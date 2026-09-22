from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.db.models import Account


class AccountRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, account_id: int) -> Account | None:
        return await self.session.get(Account, account_id)

    async def list_by_debtor(self, debtor_id: int) -> list[Account]:
        stmt = select(Account).where(Account.debtor_id == debtor_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_account(self, account: Account) -> Account:
        self.session.add(account)
        await self.session.flush()
        return account

    async def delete_account(self, account: Account) -> None:
        await self.session.delete(account)
        await self.session.flush()