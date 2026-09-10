
from sqlalchemy import select

from config.db.abstract_repository import AbstractDebtorRepository

from config.db.models import Debtor
from config.logger_config import db_logger


class DebtorAlchemyRepository(AbstractDebtorRepository):
    """Класс для работы с табдицей debtors"""
    def __init__(self, session):
        self.session = session

    async def add_debtor(self, debtor: Debtor) -> Debtor | None:
        """Добавить нового должника"""
        try:
            self.session.add(debtor)
            await self.session.refresh(debtor)  # обновить объект (например, для получения id)
            await self.session.commit()
            return debtor
        except Exception as e:
            db_logger.error(f"Ошибка сохранения должника {e}")
            await self.session.rollback()


    async def get_debtor(self, debtor_id) -> Debtor:
        stmt = select(Debtor).where(Debtor.id == debtor_id) # далее для подгрузки аккаунтов банка .selectinload(Debtor.bank_accounts)
        result = await self.session.execute(stmt)
        return result.scalars().first()


    async def update_debtor(self, debtor: Debtor) -> Debtor:
        """
        Обновить данные должника по id.
        data – словарь с полями для обновления.
        Возвращает обновлённый объект или None, если должник не найден.
        """
        # Сначала проверим, существует ли запись
        debtor = await self.get_debtor(debtor.id)
        if debtor:
            self.session.add(debtor)
            await self.session.refresh(debtor)
            return debtor


    async def delete_debtor(self, debtor_id: int) -> bool:
        """
        Удалить должника по id.
        Возвращает True, если удаление выполнено, иначе False.
        """
        debtor = await self.get_debtor(debtor_id)
        if not debtor:
            return False
        await self.session.delete(debtor)
        await self.session.commit()
        return True