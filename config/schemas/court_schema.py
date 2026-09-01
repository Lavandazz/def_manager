

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict

class CourtSessionSchema(BaseModel):
    id: int
    date_court: Optional[date] = None
    time_court: Optional[str] = None
    hall_court: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

