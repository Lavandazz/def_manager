from config.repository.db_repository import CaseAlchemyRepository


class CaseService:
    """
    Сервис для работы с репозиторием CaseAlchemyRepository.
    """
    def __init__(self, repository):
        self.repository: CaseAlchemyRepository = repository

    async def get_all_cases(self, *args,):
        return self.repository.all_cases()
        