from typing import Any, Dict
from fastapi import APIRouter, \
    Request, Depends, \
    Cookie, Header, Path, Query, Body, Form, \
    File, UploadFile, status, \
    HTTPException
from pydantic import EmailStr
from ..req.auth_validation import decrypt_meta
from ..res.response import res_success, res_err
from ...services.auth_service import AuthService
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
auth_service = AuthService(
    auth_repo=auth_repo,
    obj_storage=global_object_storage,
    email=email,
)

router = APIRouter(
    prefix='/auth-nosql',
    tags=['auth'],
    responses={404: {'description': 'Not found'}},
)


@router.get('/security/pubkey')
def get_pubkey(ts: int):
    pubkey = get_public_key(ts=ts)
    return res_success(data=pubkey)


'''send_conform_code

sendby: 
  'no_exist', # email 不存在時寄送
  'registered', # email 已註冊時寄送
'''


@router.post('/sendcode/email')
async def send_conform_code_by_email(
    email: EmailStr = Body(...),
    confirm_code: str = Body(...),
    sendby: str = Body(...),
    auth_db: Any = Depends(get_db),
    account_db: Any = Depends(get_db)
):
    res = await auth_service.send_conform_code_by_email(
        email=email,
        confirm_code=confirm_code,
        sendby=sendby,
        auth_db=auth_db,
        account_db=account_db
    )

    return res_success(data=res)


@router.post('/signup')
def signup(
    email: EmailStr = Body(...),
    # meta ex: "{\"region\":\"jp\",\"role\":\"teacher\",\"pass\":\"secret\"}"
    data: Dict = Depends(decrypt_meta),
    auth_db: Any = Depends(get_db),
    account_db: Any = Depends(get_db),
):
    res = auth_service.signup(
        email=email,
        data=data,
        auth_db=auth_db,
        account_db=account_db,
    )

    return res_success(data=res)


@router.post('/login')
def login(
    email: EmailStr = Body(...),
    # meta ex: "{\"region\":\"jp\",\"pass\":\"secret\"}"
    data: Dict = Depends(decrypt_meta),
    current_region: str = Body(...),
    auth_db: Any = Depends(get_db),
    account_db: Any = Depends(get_db),
):
    res = auth_service.login(
        email=email,
        data=data,
        current_region=current_region,
        auth_db=auth_db,
        account_db=account_db,
    )

    return res_success(data=res)
