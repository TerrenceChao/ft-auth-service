from pydantic import BaseModel, validator


class ResetPasswordPayload(BaseModel):
    aid: str
    password1: str
    password2: str

    @validator('password2')
    def passwords_match(cls, v, values, **kwargs):
        print('validate')
        if 'password1' in values and v != values['password1']:
            raise ValueError('passwords do not match')
        return v