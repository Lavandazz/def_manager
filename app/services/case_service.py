
class CaseService:
    """
    Сервис для работы с репозиторием (например CaseAlchemyRepository) для api.
    """
    def __init__(self, repository):
        self.repository = repository

    async def add_case(self, case):
        await self.repository.add_case(case)

    async def get_case(self, case_id):
        return await self.repository.get_case(case_id)

    async def get_case_documents_paginated(self, case_id: int, page: int, size: int):
        return await self.repository.get_case_documents_paginated(case_id, page, size)
    
    async def get_all_cases(self, *args,):
        return await self.repository.all_cases()
        
    async def get_user_cases(self, user_id):
        return await self.repository.get_all_cases_by_user(user_id)
    
