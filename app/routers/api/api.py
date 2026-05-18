from typing import Annotated
from fastapi import APIRouter, Depends
from services.case_service import CaseService
from config.repository.db_repository import CaseAlchemyRepository
from .dependensy import get_case_repository


router = APIRouter()


@router.get("/admin/cases")
async def get_cases(repo: Annotated[CaseAlchemyRepository, Depends(get_case_repository)]):
    """
    Отображение всех cases номеров из бд.
    Будет доступно только супер-админу
    """
    cases_service = CaseService(repo)
    return await cases_service.get_all_cases()
    

@router.get("/user/cases")
async def get_user_cases(repo: Annotated[CaseAlchemyRepository, Depends(get_case_repository)]):
    """
    Отображение всех сases текущего пользователя
    """
    cases_service = CaseService(repo)
    return await cases_service.get_user_cases()
