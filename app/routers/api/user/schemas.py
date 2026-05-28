from pydantic import BaseModel, EmailStr


class UserLogin(BaseModel):
    username: str
    telegram_id: int
    password: str
    
    email: EmailStr

class UserRegistration(UserLogin):
    second_password: str
