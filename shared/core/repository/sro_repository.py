
from sqlalchemy import select

from shared.config.db.models import Sro
from shared.config.logger_config import db_logger


class SroAlchemyRepository:
    """
    Класс для работы базой данных через SQLAlchemy.
    Запись Sro в базу данных, получение  по id
    """
    def __init__(self, session):
        self.session = session

    async def add_sro(self, sro: Sro) -> Sro | None:
        """
        Сохранение СРО в базу данных.
        Передаваемый объект должен быть экземпляром модели Sro.
        """
        try:
            self.session.add(sro)
            await self.session.commit()
            return sro

        except Exception as e:
            db_logger.exception("не удалось сохранить Sro в бд: %s", e)
            await self.session.rollback()


    async def get_sro_by_id(self, sro_id):
        """
        Получение данных из таблицы Sro по id
        param: sro_id
        """
        stmt = (
            select(Sro)
            .where(Sro.id == sro_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    
    async def get_all_sro(self) -> list[Sro]:
        """
        Получение всех СРО

        """
        stmt = select(Sro)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_sro(self, sro_id, **fields):
        """
        Получаем sro_id и словарь атрибутов fields.
        Для изменения данных sro делаем свой запрос фильтрации
        """
        sro = await self.session.get(Sro, sro_id)
        # проверяем что пришло и устанавливаем значения атрибутам
        for name, value in fields.items():
            setattr(sro, name, value)
        try:
            await self.session.commit()
        except Exception as e:
            db_logger.exception("не обновить sro %s: %s", sro_id, e)
            await self.session.rollback()
            return None


    async def delete_sro(self, param):
        pass
        