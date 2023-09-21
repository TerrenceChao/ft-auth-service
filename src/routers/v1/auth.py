from typing import Any
from fastapi import APIRouter, \
    Request, Depends, \
    Cookie, Header, Path, Query, Body, Form, \
    File, UploadFile, status, \
    HTTPException
from pydantic import EmailStr
from ..res.response import res_success, res_err
from ...services.auth_service import AuthService
from ...configs.database import get_db, get_client
from ...configs.s3 import get_s3_resource
from ...infra.utils.auth_util import get_public_key, decrypt_meta
from ...infra.db.nosql.auth_repository import AuthRepository
from ...infra.storage.global_object_storage import GlobalObjectStorage
from ...infra.apis.email import send_conform_code
import logging as log

log.basicConfig(filemode='w', level=log.INFO)

auth_repo = AuthRepository()
global_object_storage = GlobalObjectStorage(s3=get_s3_resource())
auth_service = AuthService(
    auth_repo=auth_repo,
    obj_storage=global_object_storage,
    send_conform_code=send_conform_code,
)

router = APIRouter(
    prefix="/auth-nosql",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)


@router.get("/security/pubkey")
def get_pubkey(ts: int):
    pubkey = get_public_key(ts=ts)
    return res_success(data=pubkey)


"""send_conform_code

sendby: 
  "no_exist", # email 不存在時寄送
  "registered", # email 已註冊時寄送
"""


@router.post("/sendcode/email")
async def send_conform_code_by_email(
    email: EmailStr = Body(...),
    confirm_code: str = Body(...),
    sendby: str = Body(...),
    auth_db: Any = Depends(get_db),
    account_db: Any = Depends(get_db)
):
    res, err = await auth_service.send_conform_code_by_email(
        email=email,
        confirm_code=confirm_code,
        sendby=sendby,
        auth_db=auth_db,
        account_db=account_db
    )
    if err:
        return res_err(data=res, msg=err)

    return res_success(data=res)


@router.post("/signup")
def signup(
    email: EmailStr = Body(...),
    # ex: "{\"region\":\"jp\",\"role\":\"teacher\",\"pass\":\"secret\"}"
    meta: str = Body(...),
    pubkey: str = Body(...),
    auth_db: Any = Depends(get_db),
    account_db: Any = Depends(get_db),
):
    data = decrypt_meta(meta=meta, pubkey=pubkey)
    res, err = auth_service.signup(
        email=email,
        data=data,
        auth_db=auth_db,
        account_db=account_db,
    )
    if err:
        return res_err(data=res, msg=err)

    return res_success(data=res)


@router.post("/login")
def login(
    email: EmailStr = Body(...),
    meta: str = Body(...),  # ex: "{\"region\":\"jp\",\"pass\":\"secret\"}"
    pubkey: str = Body(...),
    current_region: str = Body(...),
    auth_db: Any = Depends(get_db),
    account_db: Any = Depends(get_db),
):
    data = decrypt_meta(meta=meta, pubkey=pubkey)
    res, err = auth_service.login(
        email=email,
        data=data,
        current_region=current_region,
        auth_db=auth_db,
        account_db=account_db,
    )
    if err:
        return res_err(data=res, msg=err)

    return res_success(data=res)
