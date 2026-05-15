from typing import Annotated
from fastapi import APIRouter, Depends
from config.repository.db_repository import CaseAlchemyRepository
from .dependensy import get_case_repository


router = APIRouter()


@router.get("/ping")
async def ping():
    return {"ping": "pong!"}


@router.get("/cases")
async def get_cases(repo: Annotated[CaseAlchemyRepository, Depends(get_case_repository)]):
    cases = await repo.all_cases()
    return cases
