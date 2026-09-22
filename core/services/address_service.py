from config.db.models import Address, MailAddress, ResidentialAddress
from core.repository.address_repository import AddressRepository, ResidentialAddressRepository
from config.db.models import ResidentialAddress
from core.services.region_service import RegionService


class AddressService:
    def __init__(self, repo: AddressRepository):
        self.repo = repo

    async def create_address( self, street: str, house: str, building: str | None = None) -> Address:
        address = Address(street=street, house=house, building=building)
        return await self.repo.create_address(address)

    async def create_mail_address( self, mail_index: int, region_id: int, address_id: int ) -> MailAddress:
        mail_address = MailAddress(mail_index=mail_index, region_id=region_id, address_id=address_id)
        return await self.repo.create_mail_address(mail_address)


class ResidentialAddressService:
    """
    Сервис для работы с адресами проживания физ должников
    """
    def __init__(self, repo: ResidentialAddressRepository):
        self.repo = repo

    async def create_address(self, region_id: int | None, address_id: int, flat: int | None = None) -> ResidentialAddress:
        full_address = ResidentialAddress(region_id=region_id, address_id=address_id ,flat=flat)
        return await self.repo.create_address(full_address)

    async def list_addresses(self) -> list[ResidentialAddress]:
        return await self.repo.all_with_relations()

    async def get_address(self, address_id: int) -> ResidentialAddress | None:
        return await self.repo.get(address_id)


class MailAddressService:
    """
    Сервис для работы с почтовыми адресами
    """
    def __init__(self, region_service: RegionService, address_service: AddressService ):
        self.region_service = region_service
        self.address_service = address_service

    async def create_mail_address( self, mail_index: int, city: str, street: str, house: str, building: str | None = None, region_name: str | None = None ) -> MailAddress:
        """
        Метод принимает данные для сохранения почтового адреса.
        Сохраняет и получает id записей для региона и адреса, сохраняет почтовый адрес
        """
        # Сохраняем или получаем Регион
        region = await self.region_service.get_or_create_region(
            city=city,
            region_name=region_name,
        )
        # Сохраняем адрес
        address = await self.address_service.create_address(
            street=street,
            house=house,
            building=building,
        )
        # Передаем в сервис почтовый индекс, id региона и id адреса
        return await self.address_service.create_mail_address(            
            mail_index=mail_index,
            region_id=region.id,
            address_id=address.id
            )
    