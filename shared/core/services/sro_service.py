from shared.config.db.models import Sro
from shared.core.repository.sro_repository import SroAlchemyRepository


class SroService:
    def __init__(self, repo: SroAlchemyRepository):
        self.repo = repo

    async def create_sro(self, sro: Sro) -> Sro | None:
        return await self.repo.add_sro(sro)

    async def get_sro(self, sro_id: int) -> Sro | None:
        return await self.repo.get_sro_by_id(sro_id)

    async def get_all_sro(self) -> list[Sro]:
        return await self.repo.get_all_sro()

    async def update_sro(self, sro_id: int, **fields) -> Sro | None:
        return await self.repo.update_sro(sro_id, **fields)

    async def delete_sro(self, sro_id: int) -> bool:
        ...