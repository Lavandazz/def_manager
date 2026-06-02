from pydantic import BaseModel, EmailStr



class UserSchema(BaseModel):
    username: str
    telegram_id: int
    email: EmailStr

class UserLogin(UserSchema):
    password: str

class UserRegistration(UserLogin):
    second_password: str

class UserNameSchema(BaseModel):
    """только для ускорения в разработке"""
    username: str

