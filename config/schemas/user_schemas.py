from pydantic import BaseModel, EmailStr



# class UserSchema(BaseModel):
#     # username: str
#     telegram_id: int | None
#     email: EmailStr | None

class UserSchema(BaseModel):
    telegram_id: int | None = None   # явно None как значение по умолчанию
    email: EmailStr | None = None


class UserLogin(UserSchema):
    password: str
    

class UserRegistration(UserLogin):
    username: str
    second_password: str


class UserResponseSchema(BaseModel):
    """
    Модель для возврата объекта user и сообщения после редактирования профиля
    """
    message: str
    user: UserSchema


