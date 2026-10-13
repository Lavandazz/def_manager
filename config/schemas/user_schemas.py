import datetime

from pydantic import BaseModel, EmailStr
from datetime import date

class UserSchema(BaseModel):
    username: str
    telegram_id: int | None = None   # явно None как значение по умолчанию
    email: EmailStr | None = None

class UserUpdateSchema(BaseModel):
    """
    Валидация только для редактирования, где все поля опциональны.
    """
    username: str | None = None 
    telegram_id: int | None = None   
    email: EmailStr | None = None

class UserEfrsbSchema(BaseModel):
    """Класс используется для приема данных от парсера при обновлении данных пользователя"""
    inn: str | None = None
    snils: str | None = None
    reg_num: str | None = None
    reg_date: date | None = None
    date_begin: date | None = None

class UserSroUpdateSchema(UserUpdateSchema):
    """    Используется для добавления связи пользователя и СРО  """
    sro_id: int | None = None


class UserLogin(UserSchema):
    password: str
    

class UserRegistration(UserLogin):
    username: str
    second_password: str

class UserPasswordSchema(BaseModel):
    """Только для обновления hashed_password в БД."""
    hashed_password: str


class CaseSchema(BaseModel):
    number_case: str
    debtor: str


