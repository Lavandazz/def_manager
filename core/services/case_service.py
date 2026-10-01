
from datetime import date, datetime


class CaseService:
    """
    Сервис для работы с репозиторием (например CaseAlchemyRepository) для api.
    """
    def __init__(self, repository):
        self.repository = repository

    async def add_case(self, case: str):
        await self.repository.add_case(case)

    async def get_case(self, case_id: int):
        return await self.repository.get_case(case_id)

    async def get_case_for_documents(self, case_id: int):
        return await self.repository.get_case_for_documents(case_id)

    async def get_case_documents_paginated(self, case_id: int, page: int, size: int):
        return await self.repository.get_case_documents_paginated(case_id, page, size)

    async def get_case_by_number(self, number: str):
        case = await self.repository.find_case_by_number(number)
        return case
    
    async def get_cases(self, *args,):
        return await self.repository.get_cases()
        
    async def get_user_cases(self, user_id: int):
        return await self.repository.get_cases_by_user(user_id)

        return await self.repository.get_cases_by_type(user_id, debtor_type)

    async def update_case(self, case_id: int, attr: dict):
        return await self.repository.update_case(case_id, **attr)

    async def update_case_date(self, case_number: str, date_case: date):
        case = await self.get_case_by_number(case_number)
        if case.date_case is None:
            return await self.repository.update_date(case.id, date_case)
        return case


    async def update_case_link(self, case_number: str, link: str):
        case = await self.repository.get_case_by_number(case_number)
        if case.link is None:
            return await self.repository.update_link(case.id, link)
        return case


    async def delete_case(self, case_id: int):
        return await self.repository.delete_case(case_id)