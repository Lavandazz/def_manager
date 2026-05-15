from typing import Annotated
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from fastapi import Depends

from config.repository.db_repository import CaseAlchemyRepository
from config.db.database import UnitOfWork
from config.settings_env import settings


ADB_URL = settings.get_async_db_url()
engine = create_async_engine(url=ADB_URL)
async_sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)


async def get_db():
    unit_of_work = UnitOfWork(async_sessionmaker)
    async with unit_of_work:
        yield unit_of_work

async def get_case_repository(unit_of_work: Annotated[UnitOfWork, Depends(get_db)]):
    """
    Функция для DI в api сервисах
    """
    return CaseAlchemyRepository(unit_of_work.session)
