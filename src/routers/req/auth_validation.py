import json
from pydantic import BaseModel, validator
from typing import Optional
from decimal import Decimal
from pydantic import EmailStr
from fastapi import Body
from ...configs.constants import VALID_ROLES, REGION_MAPPING
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

REGION_CODES = set(REGION_MAPPING.values())

def decrypt_meta(
    # signup -> meta: "{\"region\":\"jp\",\"role\":\"teacher\",\"pass\":\"secret\"}"
    # login  -> meta: "{\"region\":\"jp\",\"pass\":\"secret\"}"
    meta: str = Body(...),
    pubkey: str = Body(...)
):
    try:
        meta_json = json.loads(meta)
        if 'role' in meta_json and not meta_json['role'] in VALID_ROLES:
            raise ClientException(msg=f'role allowed only in {VALID_ROLES}')
        
        if not meta_json['region'] in REGION_CODES:
            raise ClientException(msg=f'region is not allowed')

        return meta_json

    except json.JSONDecodeError as e:
        log.error(
            f'func: decrypt_meta error [json_decode_error] meta:%s, err:%s', meta, e.__str__())
        raise ClientException(msg=f'invalid json format, meta:{meta}')

    except ClientException as e:
        raise ClientException(msg=e.msg)
