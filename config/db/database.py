from contextlib import AbstractAsyncContextManager
from sqlalchemy.ext.asyncio import async_sessionmaker


class DatabaseAbstract(AbstractAsyncContextManager):
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass



class UnitOfWork(DatabaseAbstract):
    """ 
    Класс для подключения к базе данных через SQLAlchemy.
    """
    def __init__(self, session_maker):
        self.session_maker: async_sessionmaker = session_maker

    async def __aenter__(self):
        """
        Возвращаем self — объект UoW, чтобы управлять транзакцией и получать доступ к методам:
        rollback, commit.
        В DI возвращаем атрибут .session, например CaseAlchemyRepository(unit_of_work.session)
        """
        self.session = self.session_maker()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.session.rollback()
        else:
            await self.session.commit()

        await self.session.close()

    async def commit(self):
        if self.session:
            await self.session.commit()

    async def rollback(self):
        if self.session:
            await self.session.rollback()
