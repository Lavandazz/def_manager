import asyncio


from config.db.db_config import get_db
from core.repository.case_repository import CaseAlchemyRepository
from core.services.case_service import CaseService


async def det_number_cases(service: CaseService):
    """ Получение списка дел по расписанию"""
    async for unit_of_work in get_db():
        repo = CaseAlchemyRepository(unit_of_work.session)
        service = CaseService(repo)
        cases = await service.get_cases()
        return cases

