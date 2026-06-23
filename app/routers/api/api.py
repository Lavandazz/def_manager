from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from core.services.case_service import CaseService
from app.utils.dependensy import get_case_service, get_verify_user
from config.db.models import User


router = APIRouter()


@router.get("/cases", tags=["api_case"])
async def get_cases(cases_service: Annotated[CaseService, Depends(get_case_service)],
                    user: User = Depends(get_verify_user)):
    """
    Отображение всех cases номеров из бд.
    Будет доступно только супер-админу
    :param cases_service: Используется зависимость от сервиса для работы с логикой получения всех кейсов.

    """
    if user:
        cases = await cases_service.get_all_cases()
        if cases:
            return cases
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Cases не найдены')
