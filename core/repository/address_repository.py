from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from config.db.models import Address, MailAddress, ResidentialAddress


class AddressRepository:
    """Репозиторий для сохранения адреса: улица, строение, дом"""
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_address(self, address: Address) -> Address:
        self.session.add(address)
        await self.session.flush()
        return address

    async def create_mail_address(self, mail_address: MailAddress) -> MailAddress:
        self.session.add(mail_address)
        await self.session.flush()
        return mail_address


class ResidentialAddressRepository:
    """
    Репозиторий для сохранения полного адреса прописки.
    Включает в себя регион, город, улицу, строение, дом, квартиру
    """
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_address(self, address) -> ResidentialAddress:
        self.session.add(address)
        await self.session.flush() # flush нужен, чтобы получить id до commit
        return address


    async def all_with_relations(self) -> list[ResidentialAddress]:
        """Все адреса прописки с подгруженными region и address."""
        stmt = (
            select(ResidentialAddress)
            .options(
                joinedload(ResidentialAddress.region),
                joinedload(ResidentialAddress.address),
            )
            .order_by(ResidentialAddress.id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all())

    async def get(self, address_id: int) -> ResidentialAddress | None:
        stmt = (
            select(ResidentialAddress)
            .where(ResidentialAddress.id == address_id)
            .options(
                joinedload(ResidentialAddress.region),
                joinedload(ResidentialAddress.address),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().unique().first()