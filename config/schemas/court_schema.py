

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict

class CourtSessionSchema(BaseModel):
    court: str
    date_court: date
    time_court: str
    hall_court: str

    model_config = ConfigDict(from_attributes=True)
