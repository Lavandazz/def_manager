class CourtService:
    def __init__(self, repository):
        self.repository = repository

    async def get_courts(self, user_id):
        return await self.repository.get_all_courts(user_id)
    
    async def get_court_by_case(self, case_id):
        return await self.repository.get_court_by_case(case_id)
    
    async def delete_old_courts(self, date):
        return await self.repository.delete(date)