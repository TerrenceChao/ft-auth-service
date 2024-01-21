from typing import Any
from fastapi import APIRouter, Depends

from src.configs.constants import HERE_WE_ARE
from src.infra.apis.facebook import FBLoginRepository
from src.infra.apis.google import GoogleLoginRepository
from src.services.fb_auth_service import FBAuthService
from src.services.google_auth_service import GoogleAuthService
from src.routers.req.auth_validation import check_valid_role
from src.routers.res.response import res_success
from ...configs.database import get_db
from ...configs.s3 import get_s3_resource
from ...infra.db.nosql.auth_repository import AuthRepository
from ...infra.storage.global_object_storage import GlobalObjectStorage
from ...infra.apis.email import Email
import logging as log

log.basicConfig(filemode='w', level=log.INFO)

auth_repo = AuthRepository()
global_object_storage = GlobalObjectStorage(s3=get_s3_resource())
email = Email()

fb_auth_service = FBAuthService(
    auth_repo=auth_repo,
    obj_storage=global_object_storage,
    email=email,
    fb=FBLoginRepository(),  
)

google_auth_service = GoogleAuthService(
    auth_repo=auth_repo,
    obj_storage=global_object_storage,
    email=email,
    google=GoogleLoginRepository(),
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
    res = fb_auth_service.register_or_login(code, state, auth_db, account_db)
    return res_success(data=res)

@router.get('/fb/dialog')
def fb_dialog(
    role: str = Depends(check_valid_role),
):
    data = fb_auth_service.dialog(role, HERE_WE_ARE)
    return res_success(data=data)

@router.get('/google/login')
def google_registered_or_login(
    code: str,
    state: str,
    auth_db: Any = Depends(get_db),
    account_db: Any = Depends(get_db)
):
   res = google_auth_service.register_or_login(code, state, auth_db, account_db)
   return res_success(data=res)

@router.get('/google/dialog')
def google_dialog(
    role: str = Depends(check_valid_role),
):
    data = google_auth_service.dialog(role, HERE_WE_ARE)
    return res_success(data=data)
