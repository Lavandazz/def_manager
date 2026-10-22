from shared.core.repository.case_repository import CaseAlchemyRepository
from shared.core.repository.court_repository import CourtRepository
from shared.core.repository.court_session_repositoty import CourtSessionAlchemyRepository
from shared.core.repository.pars_documents_repository import ParsDocumentAlchemyRepository
from shared.core.services.case_service import CaseService
from shared.core.services.parsers.parser_saver_service import ParserDataSaver
from shared.core.services.court_service import CourtService
from shared.core.services.court_session_service import CourtSessionService
from shared.core.services.pars_document_service import ParsDocumentService




def create_parser_data_saver(session):
    """
    Фабрика для создания подключения к бд.
    """
    case_repo = CaseAlchemyRepository(session)
    court_repo = CourtRepository(session)
    court_session_repo = CourtSessionAlchemyRepository(session)
    pars_doc_repo = ParsDocumentAlchemyRepository(session)

    case_service = CaseService(case_repo)
    court_service = CourtService(court_repo)
    court_session_service = CourtSessionService(court_session_repo)
    pars_doc_service = ParsDocumentService(pars_doc_repo)

    return ParserDataSaver(
        case_service=case_service,
        court_service=court_service,
        court_session_service=court_session_service,
        pars_document_service=pars_doc_service
    )
