
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

from config.db.abstract_repository import AbstractDebtorRepository

from config.db.models import Account, Bank, Case, Debtor, MailAddress, ResidentialAddress
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

    async def get_debtor(self, user_id, debtor_id) -> Debtor | None:
        """Получаем должника, отфильтрованного по айди и пользователю"""
        stmt = (
            select(Debtor)
            .join(Debtor.cases)
            .where(Debtor.id == debtor_id, Case.id_user == user_id)
            .options(
                joinedload(Debtor.birth_region),
                joinedload(Debtor.residential_address).joinedload(ResidentialAddress.region),
                joinedload(Debtor.residential_address).joinedload(ResidentialAddress.address),
            )
        )
        return (await self.session.execute(stmt)).scalars().unique().first()

    async def get_debtor_accounts(self, debtor_id: int) -> list[Account]:
        """Получаем счета должника"""
        stmt = (
            select(Account)
            .where(Account.debtor_id == debtor_id)
            .options(
                joinedload(Account.bank).joinedload(Bank.mail_address).joinedload(MailAddress.region),
                joinedload(Account.bank).joinedload(Bank.mail_address).joinedload(MailAddress.address),
            )
        )
        return list((await self.session.execute(stmt)).scalars().unique().all())



    async def update_debtor(self, debtor: Debtor) -> Debtor | None:
        """
        Обновление данных о должнике
        Возвращает обновлённый объект или None, если должник не найден.
        """
        try:
            await self.session.commit()
            await self.session.refresh(debtor)
            return debtor
        except Exception as e:
            db_logger.error(f"Ошибка обновления должника {e}")
            await self.session.rollback()
            return None


    async def delete_debtor(self, user_id: int, debtor_id: int) -> bool:
        """
        Удалить должника по id.
        Возвращает True, если удаление выполнено, иначе False.
        """
        debtor = await self.get_debtor(user_id, debtor_id)
        if not debtor:
            return False
        await self.session.delete(debtor)
        await self.session.commit()
        return True