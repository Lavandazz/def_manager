from dataclasses import dataclass

from config.db.models import Account, Debtor
from config.schemas.debtor_schema import DebtorDetailSchema
from core.repository.debtor_repository import DebtorAlchemyRepository
from core.services.address_service import AddressService, ResidentialAddressService
from core.services.region_service import RegionService

@dataclass
class DebtorDetail:
    debtor: Debtor
    accounts: list[Account]
    
class DebtorService:
    def __init__(
        self,
        repository: DebtorAlchemyRepository,
        region_service: RegionService,                    # для сохранения региона
        address_service: AddressService,                  # для сохранения адресов
        residential_service: ResidentialAddressService,   # для сохранения полного адреса регистрации
    ):
        self.repository = repository
        self.region_service = region_service
        self.address_service = address_service
        self.residential_service = residential_service
    async def add_debtor(self, debtor):
        return await self.repository.add_debtor(debtor)


    async def get_debtor(self, user_id, debtor_id):
        """
        Получаем всю информацию по должнику: банки, счета, данные.
        # Для возврата обрабатываем в DebtorDetailSchema
        """
        debtor = await self.repository.get_debtor(user_id, debtor_id)

        if debtor is None:
            return None
        
        accounts = await self.repository.get_debtor_accounts(debtor_id)

        return DebtorDetail(debtor, accounts)


    async def update_debtor(self, user_id: int, debtor_id: int, data: dict) -> Debtor | None:
        debtor = await self.repository.get_debtor(user_id=user_id, debtor_id=debtor_id)
        if debtor is None:
            return None

        # 1. Простые поля
        simple_fields = ["debtor_type", "name", "inn", "snils", "birthday"]
        for key in simple_fields:
            value = data.get(key)
            if value is not None:
                setattr(debtor, key, value)

        # 2. Регион рождения
        birth_mode = data.get("birth_region_mode")
        print("1 ~~ birth_region_mode:", birth_mode)

        if birth_mode == "existing":
            debtor.birth_region_id = data.get("birth_region_id")

        elif birth_mode == "new":
            city = data.get("new_birth_region_city")
            region_name = data.get("new_birth_region_name")
            if city:
                region = await self.region_service.get_or_create_region(
                    city=city,
                    region_name=region_name,
                )
                debtor.birth_region_id = region.id
            print("2 ~~ birth region created, id =", debtor.birth_region_id)

        # 3. Адрес прописки  ← ОТДЕЛЬНАЯ проверка, не elif от birth!
        ra_mode = data.get("residential_address_mode")
        print("3 ~~ residential_address_mode:", ra_mode)

        if ra_mode == "existing":
            new_id = data.get("residential_address_id")
            if new_id is not None:
                # Если поле выбрано как пустое, то в бд ничего не меняем
                # Присваиваем только не пустые значения
                debtor.residential_address_id = new_id

        elif ra_mode == "new":
            # Получаем данные из формы
            street = data.get("new_ra_street")
            house = data.get("new_ra_house")
            city = data.get("new_ra_city")
            flat=int(data.get("new_ra_flat")) if data.get("new_ra_flat") else None

            if street and house and city:
                region = await self.region_service.get_or_create_region(
                    city=city,
                    region_name=data.get("new_ra_region_name"),
                )
                address = await self.address_service.create_address(
                    street=street,
                    house=house,
                    building=data.get("new_ra_building"),
                )
                ra = await self.residential_service.create_address(
                    region_id=region.id if region else None,
                    address_id=address.id,
                    flat=flat
                )
                debtor.residential_address_id = ra.id
                print("5 ~~ address id =", debtor.residential_address_id)

        # 4. Сохранение
        return await self.repository.update_debtor(debtor)

    async def delete_debtor(self, user_id: int, debtor_id: int):
        return await self.repository.delete_debtor(user_id, debtor_id)
    
