from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.db.models import Region


class RegionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_region(self, region: Region) -> Region:
        self.session.add(region)
        await self.session.flush()   # flush нужен, чтобы получить id до commit
        return region

    async def all(self) -> list[Region]:
        """Все регионы, отсортированные по названию и городу."""
        stmt = select(Region).order_by(Region.region_name, Region.city)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get(self, region_id: int) -> Region | None:
        stmt = select(Region).where(Region.id == region_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_region(self, city: str, region_name: str | None) -> Region | None:
        """Поиск региона и города"""
        stmt = select(Region)

        if region_name is None:
            stmt = stmt.where(Region.region_name.is_(None))
        else:
            stmt = stmt.where(Region.region_name == region_name)

        stmt = stmt.where(Region.city == city)

        result = await self.session.execute(stmt)
        return result.scalars().first()