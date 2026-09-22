from config.db.models import Address, Bank, MailAddress
from core.repository.address_repository import AddressRepository
from core.repository.bank_repository import BankRepository
from core.services.address_service import AddressService, MailAddressService
from core.services.region_service import RegionService


class BankService:
    def __init__(self, repo: BankRepository, mail_service: MailAddressService):
        self.repo = repo
        self.mail_service = mail_service

    async def list_banks(self) -> list[Bank]:
        return await self.repo.list_all()

    async def get_bank(self, bank_id: int) -> Bank | None:
        return await self.repo.get_by_id(bank_id)

    async def get_or_create_bank(
            self, name: str,
            mail_index: int | None = None,
            city: str | None = None,
            street: str | None = None,
            house: str | None = None,
            building: str | None = None,) -> Bank:
        """Если банка нет, необходимо создать его, в том числе сохранить адрес банка"""
        
        name = (name or "").strip()
        if not name:
            raise ValueError("Название банка обязательно")
        # Если банк уже есть — возвращаем его
        existing = await self.repo.get_by_name(name)
        if existing:
            return existing

        # Для создания нового банка, необходимо ввести и его адрес.
        # Адрес (почтовый) банка используется для генерации запросов в банки
        if not (city and street and house):
            raise ValueError(
                f"Для нового банка «{name}» нужно указать адрес: "
                f"город, улица, дом"
            )

        # Создание почтового адреса с индексом 
        mail = await self.mail_service.create_mail_address(
                mail_index=mail_index or 0,
                city=city,
                street=street, 
                house=house, 
                building=building
            )
        
        
        bank = Bank(name=name, mail_address_id=mail.id) # Связываем адрес с названием
        return await self.repo.create_bank(bank)