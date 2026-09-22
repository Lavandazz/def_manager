import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from config.schemas.court_schema import CourtSessionSchema

from config.schemas.documents_schema import ParsDocumentSchema
from config.schemas.user_schemas import UserSchema


class Case(BaseModel):
    number: str
    date: datetime.date


class DebtorSchema(BaseModel):
    name: str
    inn: int | None
    snils: str | None
    birthday: datetime.date | None

    model_config = ConfigDict(from_attributes=True)


class CaseSchema(BaseModel):
    id: int
    number_case: str
    status: int
    debtor_id: int
    debtor_name: Optional[str] = None
    debtor: DebtorSchema
    # user: UserSchema
    # pars_documents: Optional[List[ParsDocumentSchema]] = None
    # court_sessions: Optional[List[CourtSessionSchema]] = None

    model_config = ConfigDict(from_attributes=True)


