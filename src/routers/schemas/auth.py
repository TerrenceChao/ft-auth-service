from pydantic import BaseModel, validator
from typing import Optional

class ResetPasswordPayload(BaseModel):
    aid: str
    origin_password: Optional[str] = None
    password1: str
    password2: str

    @validator('password2')
    def passwords_match(cls, v, values, **kwargs):
        if 'password1' in values and v != values['password1']:
            raise ValueError('passwords do not match')
        return v