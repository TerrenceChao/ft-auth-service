from typing import Any
from fastapi import APIRouter, \
    Request, Depends, \
    Cookie, Header, Path, Query, Body, Form, \
    File, UploadFile, status, \
    HTTPException
from pydantic import EmailStr

from src.configs.constants import AccountType, HERE_WE_ARE
from src.infra.apis.facebook import FBLoginRepository
from ..res.response import res_success, res_err
from ...services.sso_service import SSOService
from ...configs.database import get_db, get_client
from ...configs.s3 import get_s3_resource
from ...infra.utils.auth_util import get_public_key
from ...infra.db.nosql.auth_repository import AuthRepository
from ...infra.storage.global_object_storage import GlobalObjectStorage
from ...infra.apis.email import Email
import logging as log

log.basicConfig(filemode='w', level=log.INFO)

auth_repo = AuthRepository()
global_object_storage = GlobalObjectStorage(s3=get_s3_resource())
email = Email()
sso_service = SSOService(
    auth_repo=auth_repo,
    obj_storage=global_object_storage,
    email=email,
)

router = APIRouter(
    prefix='/auth-nosql',
    tags=['auth'],
    responses={404: {'description': 'Not found'}},
)

# register and sign up at same api
@router.get('/fb/login')
def registered_or_login(
    code: str,
    state: str,
    auth_db: Any = Depends(get_db),
    account_db: Any = Depends(get_db)
):
    fb = FBLoginRepository()
    oauth_data = fb.oauth(code)
    if not oauth_data or not oauth_data.access_token:
        return f'there is no accesstoken \n {oauth_data}'
    user_info = fb.get_user_info(access_token=oauth_data.access_token)
    user_info.email = 'poasafddtrwe@gmail.asdfadsf'
    return sso_service.register_or_login(user_info, state, AccountType.FB, auth_db, account_db)

@router.get('/fb/dialog')
def dialog(
    role: str = '',
):
    fb = FBLoginRepository()
    return fb.dialog(role, HERE_WE_ARE)
