from core.repository.debtor_repository import DebtorRepository


class DebtorService:
    def __init__(self, repository: DebtorRepository):
        self.repository = repository

    async def add_debtor(self, debtor):
        await self.repository.add_debtor(debtor)


    async def get_debtor(self, debtor_id):
        debtor = await self.repository.get_debtor(debtor_id)
        if not debtor:
            return None
        
        return debtor

    async def update_debtor(self, debtor_id, data: dict):
        debtor = await self.get_debtor(debtor_id) # проверяем, существует ли должник
        if not debtor:
            return None
        
        for key, value in data.items():
            if hasattr(debtor, key) and value is not None:
                setattr(debtor, key, value)
                print("Поля для измнения данных:", debtor_id, debtor,key, value)
        
        return await self.repository.update_debtor(debtor)


    async def delete_debtor(self, debtor_id):
        return await self.repository.delete_debtor(debtor_id)
    
