
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ParsDocumentSchema(BaseModel):
    id: int
    date: Optional[str] = None
    declarer: Optional[str] = None
    document: Optional[str] = None
    status: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
