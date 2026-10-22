import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

# from config.schemas.debtor_schema import DebtorSchema



class CasePatch(BaseModel):
    number_case: str | None = None
    link: str | None = None
    id_user: int | None = None
    debtor_name: str | None = None
    status: int | None = None

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


