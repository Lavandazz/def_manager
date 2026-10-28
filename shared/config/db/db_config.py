from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from shared.config.settings_env import settings
from shared.config.db.database import UnitOfWork


ADB_URL = settings.get_async_db_url()
# poolclass=NullPool - Вместо того чтобы повторно использовать уже открытые соединения, 
# оно каждый раз открывает новое физическое соединение с базой данных 5
# и сразу закрывает его после использования
# Необходимо для корректной работы бд для fastapi, парсеров ефрсб и кад, 
# так как парсеры работают в своих event_loop
engine = create_async_engine(url=ADB_URL, poolclass=NullPool)
async_sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)


async def get_db():
    unit_of_work = UnitOfWork(async_sessionmaker)
    async with unit_of_work:
        yield unit_of_work
