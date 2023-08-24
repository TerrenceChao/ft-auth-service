import json
from typing import List, Dict, Any
from fastapi import APIRouter, \
    Request, Depends, \
    Cookie, Header, Path, Query, Body, Form, \
    File, UploadFile, status, \
    HTTPException
from pydantic import EmailStr
from ..res.response import res_success, res_err
from ...services.auth_service import AuthService
from ...common.auth_util import get_public_key, decrypt_meta
from ...common.global_object_storage import get_global_object_storage
from ...db.nosql.database import get_db, get_client
from ...db.nosql.auth_repository import AuthRepository
from ..exceptions import BusinessEception
import logging as log
log.basicConfig(level=log.INFO)

auth_service = AuthService(auth_repo=AuthRepository())

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
def send_conform_code_by_email(
    email: EmailStr = Body(...),
    confirm_code: str = Body(...),
    sendby: str = Body(...),
    auth_db: Any = Depends(get_db),
    account_db: Any = Depends(get_db)
):
    res, err = auth_service.send_conform_code_by_email(
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
    meta: str = Body(...), # ex: "{\"region\":\"jp\",\"role\":\"teacher\",\"pass\":\"secret\"}"
    pubkey: str = Body(...),
    auth_db: Any = Depends(get_db),
    account_db: Any = Depends(get_db),
    obj_storage: Any = Depends(get_global_object_storage)
):
    data = decrypt_meta(meta=meta, pubkey=pubkey)
    res, err = auth_service.signup(
        email=email,
        data=data,
        auth_db=auth_db,
        account_db=account_db,
        obj_storage=obj_storage
    )
    if err:
        return res_err(data=res, msg=err)
    
    return res_success(data=res)


@router.post("/login")
def login(
    email: EmailStr = Body(...),
    meta: str = Body(...), # ex: "{\"region\":\"jp\",\"role\":\"teacher\",\"pass\":\"secret\"}"
    pubkey: str = Body(...),
    client_region: str = Body(...),
    auth_db: Any = Depends(get_db),
    account_db: Any = Depends(get_db),
    obj_storage: Any = Depends(get_global_object_storage)
):
    data = decrypt_meta(meta=meta, pubkey=pubkey)
    res, err = auth_service.login(
        email=email,
        data=data,
        client_region=client_region,
        auth_db=auth_db,
        account_db=account_db,
        obj_storage=obj_storage
    )
    if err:
        return res_err(data=res, msg=err)
    
    return res_success(data=res)
 

