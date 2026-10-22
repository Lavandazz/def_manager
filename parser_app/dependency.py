from shared.core.repository.case_repository import CaseAlchemyRepository
from shared.core.repository.court_repository import CourtRepository
from shared.core.repository.court_session_repositoty import CourtSessionAlchemyRepository
from shared.core.repository.pars_documents_repository import ParsDocumentAlchemyRepository
from shared.core.repository.sro_repository import SroAlchemyRepository
from shared.core.repository.user_repository import UserAlchemyRepository
from shared.core.services.case_service import CaseService
from shared.core.services.parsers.parser_saver_service import ParserDataSaver
from shared.core.services.court_service import CourtService
from shared.core.services.court_session_service import CourtSessionService
from shared.core.services.pars_document_service import ParsDocumentService
from shared.core.services.parsers.parser_sro_service import ParserSroDataSaver
from shared.core.services.sro_service import SroService
from shared.core.services.user_service import UserService



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


def create_parser_sro_data_saver(session):
    """
    Фабрика для создания подключения к бд.
    """
    user_repo = UserAlchemyRepository(session)
    sro_repo = SroAlchemyRepository(session)

    sro_service = SroService(sro_repo)
    user_service = UserService(user_repo)


    return ParserSroDataSaver(
        sro_service=sro_service,
        user_service=user_service
    )