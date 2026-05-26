from pydantic import BaseModel, EmailStr


class UserLogin(BaseModel):
    username: str
    password: str
    email: EmailStr

class UserRegistration(UserLogin):
    second_password: str
