
from contextlib import AbstractAsyncContextManager
from sqlalchemy.orm import sessionmaker



class DatabaseAbstract(AbstractAsyncContextManager):
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass



class SqlAlchemyDatabase(DatabaseAbstract):
    """ 
    Класс для работы с базой данных через SQLAlchemy.
    """
    async def __init__(self, session_maker):
        self.session_maker: sessionmaker = session_maker

    async def __aenter__(self):
        self.session = self.session_maker()
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.session.rollback()
        else:
            self.session.commit()

        self.session.close()

    async def commit(self):
        if self.session:
            self.session.commit()

    async def rollback(self):
        if self.session:
            self.session.rollback()
