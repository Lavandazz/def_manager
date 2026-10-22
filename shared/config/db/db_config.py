from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from shared.config.settings_env import settings
from shared.config.db.database import UnitOfWork


ADB_URL = settings.get_async_db_url()
engine = create_async_engine(url=ADB_URL)
async_sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)


async def get_db():
    unit_of_work = UnitOfWork(async_sessionmaker)
    async with unit_of_work:
        yield unit_of_work
