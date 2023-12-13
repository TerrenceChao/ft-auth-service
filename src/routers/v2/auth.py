from typing import Any
from fastapi import APIRouter, \
    Request, Depends, \
    Cookie, Header, Path, Query, Body, Form, \
    File, UploadFile, status, \
    HTTPException
from pydantic import EmailStr

from src.configs.constants import AccountType, HERE_WE_ARE
from src.infra.apis.facebook import FBLoginRepository
from src.infra.apis.google import GoogleLoginRepository
from ..res.response import res_success, res_err
from ...services.sso_service import SSOService, SSORepositories
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
sso_repositories = SSORepositories(
    fb = FBLoginRepository(),
    google = GoogleLoginRepository(),
)
sso_service = SSOService(
    auth_repo=auth_repo,
    obj_storage=global_object_storage,
    email=email,
    sso_repositories=sso_repositories,
)

router = APIRouter(
    prefix='/auth-nosql',
    tags=['auth'],
    responses={404: {'description': 'Not found'}},
)

# register and sign up at same api
@router.get('/fb/login')
def fb_registered_or_login(
    code: str,
    state: str,
    auth_db: Any = Depends(get_db),
    account_db: Any = Depends(get_db)
):
    return sso_service.fb_register_or_login(code, state, auth_db, account_db)

@router.get('/fb/dialog')
def fb_dialog(
    role: str = '',
):
    return sso_service.fb_dialog(role, HERE_WE_ARE)

@router.get('/google/login')
def google_registered_or_login(
    code: str,
    state: str,
    auth_db: Any = Depends(get_db),
    account_db: Any = Depends(get_db)
):
   return sso_service.google_register_or_login(code, state, auth_db, account_db)

@router.get('/google/dialog')
def google_dialog(
    role: str = '',
):
    return sso_service.google_dialog(role, HERE_WE_ARE)
