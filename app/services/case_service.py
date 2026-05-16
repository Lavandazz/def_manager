
class CaseService:
    """
    Сервис для работы с репозиторием (например CaseAlchemyRepository) для api.
    """
    def __init__(self, repository):
        self.repository = repository

    async def get_all_cases(self, *args,):
        return await self.repository.all_cases()
        