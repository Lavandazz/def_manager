from dataclasses import dataclass

from config.db.models import Account, Debtor
from config.schemas.debtor_schema import DebtorDetailSchema
from core.repository.debtor_repository import DebtorAlchemyRepository
from core.services.address_service import ResidentialAddressService
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
        residential_service: ResidentialAddressService,   # для сохранения адресов
    ):
        self.repository = repository
        self.region_service = region_service
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
        # Валидируем в пайдантик схемы
        # return DebtorDetailSchema.model_validate({
        #     "debtor": debtor,
        #     "accounts": accounts,
        # })

    async def update_debtor(self,user_id: int,debtor_id: int, data: dict) -> Debtor | None:
        """
        Обновить данные должника по id.
        data – словарь с полями для обновления.
        Возвращает обновлённый объект или None, если должник не найден.
        """
        debtor = await self.repository.get_debtor(user_id=user_id, debtor_id=debtor_id)
        if debtor is None:
            return None

        # Меняем только те поля, которые пришли и не None
        simple_fields = ["debtor_type", "name", "inn", "snils", "birthday"]
        for key in simple_fields:
            value = data.get(key)
            if value is not None:
                setattr(debtor, key, value)

        # 3. Регион рождения
        mode = data.get("birth_region_mode")
        if mode == "new":
            region = await self.region_service.get_or_create_region(
                city=data.get("new_birth_region_city"),
                region_name=data.get("new_birth_region_name"),
            )
            debtor.birth_region_id = region.id

        elif mode == "new":
            # 4.1. Регион для адреса
            region = await self.region_service.get_or_create_region(
                city=data.get("new_ra_city"),
                region_name=data.get("new_ra_region_name"),
            )
            # 4.2. Сам адрес
            address = await self.residential_service.create_address(
                region_id=region.id if region else None,
                street=data.get("new_ra_street"),
                house=data.get("new_ra_house"),
                building=data.get("new_ra_building"),
            )
            # 4.3. Привязка к должнику
            debtor.residential_address_id = address.id if address else None
            # flat (квартира) — если хранится в Debtor, а не в ResidentialAddress,
            # добавь поле отдельно; иначе сохрани в ResidentialAddress

        # 5. Отдаём в репозиторий
        return await self.repository.update_debtor(debtor)


    async def delete_debtor(self, user_id: int, debtor_id: int):
        return await self.repository.delete_debtor(user_id, debtor_id)
    
