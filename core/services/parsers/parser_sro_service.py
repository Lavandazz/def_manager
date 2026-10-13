
from config.db.models import Sro, User
from config.schemas.user_schemas import UserEfrsbSchema
from core.services.sro_service import SroService
from core.services.user_service import UserService
from utils.helper import text_helper
from config.logger_config import efrsb_logger


class ParserSroDataSaver:
    """Фасад для сохранения данных о судов, документов"""
    def __init__(
        self,
        sro_service: SroService,
        user_service: UserService
    ):
        self.sro_service = sro_service
        self.user_service = user_service

    async def save_user_data(self, user_id: int, user_data: dict) -> User:
        user = await self.user_service.get_user_by_id(user_id=user_id)  
        if user is None:
        # либо исключение
            raise ValueError(f"Пользователь с id={user_id} не найден")
        # Приводим  dict к Pydantic-схеме
        parsed = UserEfrsbSchema(
            inn=user_data.get("inn"),
            snils=user_data.get("snils"),
            reg_num=user_data.get("reg_num"),
            reg_date=text_helper.return_date(user_data.get("reg_date") or ""),
            date_begin=text_helper.return_date(user_data.get("date_begin") or ""),
        )

        # Обновляем данные пользователя
        return await self.user_service.update_user(user=user, user_data=parsed)

    async def save_sro(self, sro_data: dict) -> Sro | None:
        sro = Sro(
                    name=sro_data.get("name"),
                    reg_num=sro_data.get("reg_num"),
                    reg_date=text_helper.return_date(date_str=sro_data.get("reg_date")),
                    inn=sro_data.get("inn"),
                    ogrn=sro_data.get("ogrn"),
                    ur_address_sro=sro_data.get("ur_address_sro"),

                    phone=sro_data.get("phone"),
                    email=sro_data.get("email"),
                    url=sro_data.get("url"),
                )
        
        return await self.sro_service.create_sro(sro)

    async def save_sro_to_user(self, sro: Sro, user_id: int) -> bool :
        user = await self.user_service.get_user_by_id(user_id=user_id)
        if not user:
            efrsb_logger.error(f"Ошибка: пользователь с id {user_id} не найден")
            return False
        
        await self.user_service.attach_user_to_sro(user.id, sro_id=sro.id)
        efrsb_logger.debug(f"ParserSroDataSaver: СРО {sro.name} сохранено для пользователя {user.username}")
        
        return True

    async def save_user_sro_data(self, sro_data: dict, user_id: int) -> bool:
        """
        Метод объединяет сохранение СРО и привязку к пользователю
        """
        sro = await self.save_sro(sro_data)
        if not sro:
            return False

        await self.save_sro_to_user(sro, user_id)
        efrsb_logger.debug("Сохранены данные для пользователя и СРО")

        return True

