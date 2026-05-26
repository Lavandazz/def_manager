from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from app.services.case_service import CaseService
from app.utils.dependensy import get_case_repository


from config.repository.case_repository import CaseAlchemyRepository



router = APIRouter()


@router.get("/cases")
async def get_cases(repo: Annotated[CaseAlchemyRepository, Depends(get_case_repository)]):
    """
    Отображение всех cases номеров из бд.
    Будет доступно только супер-админу
    """
    cases_service = CaseService(repo)
    cases = await cases_service.get_all_cases()
    if cases:
        return cases
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Cases не найдены')
