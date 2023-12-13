from pydantic import BaseModel

class StatePayload(BaseModel):
    verified_code: str = 'verified_code'
    role: str
    region: str

class GeneralUserInfo(BaseModel):
    id: str
    email: str