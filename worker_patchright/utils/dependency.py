
from shared.core.repository.sro_repository import SroAlchemyRepository
from shared.core.repository.user_repository import UserAlchemyRepository
from shared.core.services.parsers.parser_sro_service import ParserSroDataSaver
from shared.core.services.sro_service import SroService
from shared.core.services.user_service import UserService


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