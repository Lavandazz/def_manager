from config.db.models import Region
from core.repository.region_repository import RegionRepository



class RegionService:
    def __init__(self, repo: RegionRepository):
        self.repo = repo

    async def get_or_create_region(self, city: str, region_name: str | None) -> Region:
        """
        Проверяем наличие региона и города.
        Возвращаем из базы если нашли или создаем запись
        """
        city = city.strip().capitalize()
        region_name = (region_name or "").strip().capitalize() or None
        existing = await self.repo.get_region(region_name=region_name,city=city)
        if existing:
            return existing

        region = Region(region_name=region_name, city=city)
        return await self.repo.create_region(region)


    async def list_regions(self) -> list[Region]:
        return await self.repo.all()

    async def get_region(self, region_id: int) -> Region | None:
        return await self.repo.get(region_id)