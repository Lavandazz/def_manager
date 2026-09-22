from config.db.models import Address, ResidentialAddress
from core.repository.address_repository import AddressRepository, ResidentialAddressRepository
from config.db.models import ResidentialAddress


class AddressService:
    def __init__(self, repo: AddressRepository):
        self.repo = repo

    async def create_address( self, street: str, house: str, building: str | None = None) -> Address:
        address = Address(street=street, house=house, building=building)
        return await self.repo.create_address(address)


class ResidentialAddressService:
    def __init__(self, repo: ResidentialAddressRepository):
        self.repo = repo

    async def create_address(self,region_id: int | None,address_id: int,flat: int | None = None) -> ResidentialAddress:
        full_address = ResidentialAddress(region_id=region_id, address_id=address_id ,flat=flat)
        return await self.repo.create_address(full_address)

    async def list_addresses(self) -> list[ResidentialAddress]:
        return await self.repo.all_with_relations()

    async def get_address(self, address_id: int) -> ResidentialAddress | None:
        return await self.repo.get(address_id)

