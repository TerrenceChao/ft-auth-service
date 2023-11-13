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
    # meta: "{\"role\":\"teacher\",\"pass\":\"secret\"}"
    meta: str = Body(...),
    pubkey: str = Body(...)
):
    try:
        # TODO: need pubkey to decrypt meta
        meta_dict = json.loads(meta)
        if not 'role' in meta_dict:
            raise ClientException(msg=f'role is required')
        
        if not meta_dict['role'] in VALID_ROLES:
            raise ClientException(msg=f'role allowed only in {VALID_ROLES}')
        
        if not 'pass' in meta_dict:
            raise ClientException(msg=f'pass is required')
        
        meta_dict['region'] = HERE_WE_ARE

        return meta_dict

    except json.JSONDecodeError as e:
        log.error(
            f'func: decrypt_meta_for_signup error [json_decode_error] meta:%s, err:%s', meta, e.__str__())
        raise ClientException(msg=f'invalid json format, meta:{meta}')

    except ClientException as e:
        raise ClientException(msg=e.msg)
    
    
def decrypt_meta_for_login(
    # meta: "{\"pass\":\"secret\"}"
    meta: str = Body(...),
    pubkey: str = Body(...)
):
    try:
        meta_dict = json.loads(meta)
        if not 'pass' in meta_dict:
            raise ClientException(msg=f'pass is required')

        return meta_dict

    except json.JSONDecodeError as e:
        log.error(
            f'func: decrypt_meta_for_login error [json_decode_error] meta:%s, err:%s', meta, e.__str__())
        raise ClientException(msg=f'invalid json format, meta:{meta}')

    except ClientException as e:
        raise ClientException(msg=e.msg)
    
    
def decrypt_meta_for_update_password(
    register_email: EmailStr = Body(...),
    # meta: "{\"password1\":\"new_pass\",\"password2\":\"new_pass\",\"origin_password\":\"password\"}"
    meta: str = Body(...),
    pubkey: str = Body(...)
) -> (ResetPasswordPayload):
    try:
        meta_dict = json.loads(meta)
        if not 'password1' in meta_dict:
            raise ClientException(msg=f'password1 is required')
        
        if not 'password2' in meta_dict:
            raise ClientException(msg=f'password2 is required')

        meta_dict.update({'register_email': register_email})
        return ResetPasswordPayload.parse_obj(meta_dict)
    
    except json.JSONDecodeError as e:
        log.error('func: decrypt_meta_for_update_password error [json_decode_error] meta:%s, err:%s', meta, e.__str__())
        raise ClientException(msg=f'invalid json format, meta:{meta}')
    
    except ClientException as e:
        raise ClientException(msg=e.msg)
