import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

# from config.schemas.debtor_schema import DebtorSchema



class Case(BaseModel):
    number: str
    date: datetime.date


class DebtorSchema(BaseModel):
    name: str
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


