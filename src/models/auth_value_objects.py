from pydantic import BaseModel, EmailStr


class AccountVO(BaseModel):
    email: EmailStr
    region: str
    role: str
    role_id: int
    created_at: int
    refresh_token: str
