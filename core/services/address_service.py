from config.db.models import ResidentialAddress
from core.repository.address_repository import ResidentialAddressRepository
from config.db.models import ResidentialAddress


class ResidentialAddressService:
    def __init__(self, repo: ResidentialAddressRepository):
        self.repo = repo

    async def create_address(self, region_id: int | None, street: str, house: str, building: str | None) -> ResidentialAddress:
        address = ResidentialAddress(region_id=region_id, street=street, house=house, building=building)
        return await self.repo.create_address(address)

    async def list_addresses(self) -> list[ResidentialAddress]:
        return await self.repo.all_with_relations()

    async def get_address(self, address_id: int) -> ResidentialAddress | None:
        return await self.repo.get(address_id)