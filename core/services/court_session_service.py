from core.repository.court_session_repositoty import CourtSessionAlchemyRepository


class CourtSessionService:
    def __init__(self, repository: CourtSessionAlchemyRepository):
        self.repository = repository

    async def add_court(self, court_session):
        # Проверяем, нет ли уже такого заседания
        print("Принял схему и проверяю", court_session)
        exists = await self.repository.exists_court_session(
            case_id=court_session.id_case,
            court_id=court_session.court_id,
            date_court=court_session.date_court,
            time_court=court_session.time_court,
            hall_court=court_session.hall_court
        )
        if exists:
            print("такой суд уже в базе есть")
            # Логируем или просто возвращаем None 
            # return await self.repository.get_court_session(...)
            return None
        # Если данных нет, сохраняем
        print("сохраняю дату суда")
        return await self.repository.add_court(court_session)

    async def get_courts(self, user_id):
        return await self.repository.get_all_courts(user_id)
    
    async def get_court_by_case(self, case_id):
        return await self.repository.get_court_by_case(case_id)
    
    async def delete_old_courts(self, date):
        return await self.repository.delete(date)