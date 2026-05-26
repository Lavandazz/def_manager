class TokenService:
    """
    Класс для работы с черным списком токенов.
    Принимается репозиторий, например TokenAlchemyRepository
    Выполняет методы проверки наличия токена в черном списке
    """

    def __init__(self, repository):
        self.repository = repository

    async def add_token(self, token: str):
        """Добавление токена в черный список"""
        await self.repository.add(token)

    async def is_token_black(self, token: str):
        """Проверка токена в черном листе"""
        return await self.repository.exists(token)
