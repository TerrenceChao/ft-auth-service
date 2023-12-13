import json
from pydantic import BaseModel, validator
from typing import Optional
from decimal import Decimal
from pydantic import EmailStr
from fastapi import Body
from ...configs.constants import VALID_ROLES, HERE_WE_ARE
from ...configs.exceptions import *
import logging as log

log.basicConfig(filemode='w', level=log.INFO)


class ResetPasswordPayload(BaseModel):
    register_email: EmailStr
    origin_password: Optional[str] = None
    password1: str
    password2: str

    @validator('password2')
    def passwords_match(cls, v, values, **kwargs):
        if 'password1' in values and v != values['password1']:
            raise ClientException(msg='passwords do not match')
        return v


def decrypt_meta_for_signup(
    # signup -> meta: "{\"role\":\"teacher\",\"pass\":\"secret\"}"
    meta: str = Body(...),
    pubkey: str = Body(...)
):
    try:
        # TODO: need pubkey to decrypt meta
        meta_json = json.loads(meta)
        if not 'role' in meta_json:
            raise ClientException(msg=f'role is required')
        
        check_valid_role(meta_json['role'])

        if not 'pass' in meta_json:
            raise ClientException(msg=f'pass is required')
        
        meta_json['region'] = HERE_WE_ARE

        return meta_json

    except json.JSONDecodeError as e:
        log.error(
            f'func: decrypt_meta_for_signup error [json_decode_error] meta:%s, err:%s', meta, e.__str__())
        raise ClientException(msg=f'invalid json format, meta:{meta}')

    except ClientException as e:
        raise ClientException(msg=e.msg)
    
    
def decrypt_meta(
    # meta: "{\"pass\":\"secret\"}"
    meta: str = Body(...),
    pubkey: str = Body(...)
):
    try:
        meta_json = json.loads(meta)
        if not 'pass' in meta_json:
            raise ClientException(msg=f'pass is required')

        return meta_json

    except json.JSONDecodeError as e:
        log.error(
            f'func: decrypt_meta error [json_decode_error] meta:%s, err:%s', meta, e.__str__())
        raise ClientException(msg=f'invalid json format, meta:{meta}')

    except ClientException as e:
        raise ClientException(msg=e.msg)

def check_valid_role(role: str) -> None:
    if not role in VALID_ROLES:
        raise ClientException(msg=f'role allowed only in {VALID_ROLES}')