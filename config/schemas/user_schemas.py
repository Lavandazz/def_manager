from pydantic import BaseModel, EmailStr


class UserSchema(BaseModel):
    username: str
    telegram_id: int | None = None   # явно None как значение по умолчанию
    email: EmailStr | None = None

class UserUpdateSchema(BaseModel):
    """ Валидация только для редактирования, где все поля опциональны """
    username: str | None = None 
    telegram_id: int | None = None   
    email: EmailStr | None = None


class UserLogin(UserSchema):
    password: str
    

class UserRegistration(UserLogin):
    username: str
    second_password: str

class UserPasswordSchema(BaseModel):
    """Только для обновления hashed_password в БД."""
    hashed_password: str


class UserResponseSchema(BaseModel):
    """
    Модель для возврата объекта user и сообщения после редактирования профиля
    """
    message: str
    user: UserSchema


class CaseSchema(BaseModel):
    number_case: str
    debtor: str

class CaseResponseSchema(BaseModel):
    message: str
    case: CaseSchema


