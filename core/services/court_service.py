class CourtService:
    def __init__(self, repository):
        self.repository = repository

    async def get_or_create_court(self, court_name):
        return await self.repository.get_or_create_court(court_name)
    
    async def get_court(self, court_name):
        return await self.repository.get_court(court_name)
