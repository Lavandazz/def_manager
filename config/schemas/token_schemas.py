from pydantic import BaseModel

class AuthTokenSchema(BaseModel):
    id: int
    email: str | None = None
    telegram_id: int | None = None
