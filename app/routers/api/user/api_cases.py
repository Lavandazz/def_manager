
from fastapi import APIRouter, Depends, HTTPException, status

from app.services.case_service import CaseService

from app.utils.dependensy import get_case_service, get_verify_user
from config.db.models import User, Case
from config.logger_config import profile_logger
from config.schemas.user_schemas import CaseResponseSchema, CaseSchema


router = APIRouter()


@router.get("/cases", tags=["api_case"])
async def get_user_cases(
    user: User = Depends(get_verify_user),
    case_service: CaseService = Depends(get_case_service)
    ):
    """
    Для отладки передаем id пользователя.
    В последствии заменить на email
    """
    cases = await case_service.get_user_cases(user_id=user.id)

    if cases:
        return {
            "cases": cases,
        }
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Данных нет или нет зарегистрированных дел')


@router.post("/cases/add_case", tags=["api_case"])
async def add_case(
    case: CaseSchema,
    user: User = Depends(get_verify_user),
    case_service: CaseService = Depends(get_case_service)
):
    if user:
        new_case = Case(
            number_case=case.number_case,
            debtor=case.debtor,
            id_user=user.id
        )
        exist_case = await case_service.add_case(new_case)
        profile_logger.info("Добавлено новое дело: %s", exist_case)

        return {"message": "Дело успешно добавлено", "case": exist_case}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Пользователь не найден')
