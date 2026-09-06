from config.db.models import CourtSession
from core.services.case_service import CaseService
from core.services.court_service import CourtService
from core.services.court_session_service import CourtSessionService
from core.services.pars_document_service import ParsDocumentService


class ParserDataSaver:
    """Фасад для сохранения данных о судов, документов"""
    def __init__(
        self,
        case_service: CaseService,
        court_service: CourtService,
        court_session_service: CourtSessionService,
        pars_document_service: ParsDocumentService
    ):
        self.case_service = case_service
        self.court_service = court_service
        self.court_session_service = court_session_service
        self.pars_document_service = pars_document_service

    async def _get_id_case(self, case_number):
        return await self.case_service.get_case_by_number(case_number)

    async def save_court_data(self, court_name, case_number, date_court, time_court, hall_court):
        court = await self.court_service.get_or_create_court(court_name) # получаем или сохраняем наименование суда
        case = await self._get_id_case(case_number)
        if not court:
            print("ошибка в сохранении или получении наименования суда")
            return None
        if not case:
            print(f"Ошибка: дело {case_number} не найдено")
            return None
    
        court_data: CourtSession = CourtSession(
            id_case=case.id, 
            date_court=date_court, 
            hall_court=hall_court, 
            time_court=time_court, 
            court_id=court.id
            )
        print("ParserDataSaver: сохранил court_data")
        await self.court_session_service.add_court(court_session=court_data)
        
