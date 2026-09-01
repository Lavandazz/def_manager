from datetime import date

from pydantic import BaseModel



class DebtorSchema(BaseModel):
    name: str
    inn: int
    snils: str
    birthday: date


