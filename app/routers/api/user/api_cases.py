from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status

from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.services.case_service import CaseService
from app.services.token_service import TokenService
from app.services.user_service import UserService
from app.utils.auth.auth_token import AuthTokenService
from app.utils.auth.password_hasher import PasswordHasher
from app.utils.dependensy import get_case_service, get_token_service, get_user_service, get_verify_user

from config.db.models import User
from config.logger_config import profile_logger
from config.schemas.token_schemas import AuthTokenSchema
from config.schemas.user_schemas import UserLogin, UserRegistration


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
