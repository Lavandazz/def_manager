from pydantic import BaseModel, EmailStr



class UserSchema(BaseModel):
    # username: str
    telegram_id: int | None
    email: EmailStr | None

class UserLogin(UserSchema):
    password: str

class UserRegistration(UserLogin):
    username: str
    second_password: str

class UserNameSchema(BaseModel):
    """только для ускорения в разработке"""
    username: str

