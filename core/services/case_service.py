
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

    async def get_case_documents_paginated(self, case_id: int, page: int, size: int):
        return await self.repository.get_case_documents_paginated(case_id, page, size)

    async def get_case_by_number(self, number: str):
        case = await self.repository.find_case_by_number(number)
        return case
    
    async def get_cases(self, *args,):
        return await self.repository.get_cases()
        
    async def get_user_cases(self, user_id: int):
        return await self.repository.get_cases_by_user(user_id)

    async def get_user_cases_by_type(self, user_id: int, debtor_type):
        return await self.repository.get_cases_by_type(user_id, debtor_type)

    async def update_case(self, case_id: int, attr: dict):
        return await self.repository.update_case(case_id, **attr)

    async def update_case_link(self, case_number: str, link: str):
        case = await self.repository.get_case_by_number(case_number)
        if case.link == None:
            print(f"Сохраняю ссылку на дело {case_number}: {link}")
            return await self.repository.update_link(case.id, link)
        print(f"Ссылка на дело {case_number} уже существует: {case.link}")
        return True


    async def delete_case(self, case_id: int):
        return await self.repository.delete_case(case_id)