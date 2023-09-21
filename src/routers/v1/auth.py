import json
from typing import List, Dict, Any
from fastapi import APIRouter, \
    Request, Depends, \
    Cookie, Header, Path, Query, Body, Form, \
    File, UploadFile, status, \
    HTTPException
from pydantic import EmailStr
from ..res.response import res_success, res_err
from ...common.auth_util import get_public_key, decrypt_meta, \
    gen_random_string, gen_account_data, \
    match_password, filter_by_keys
from ...common.global_object_storage import get_global_object_storage
from ...common.email_util import send_conform_code
from ...db.nosql.database import get_db, get_client
from ...db.nosql import schemas, auth_repository
from ..exceptions import BusinessEception
from ..schemas.auth import ResetPasswordPayload
import logging as log

log.basicConfig(level=log.INFO)


auth_repo = auth_repository.AuthRepository()


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

    res, err = auth_repo.get_account_by_email(
        auth_db=auth_db, account_db=account_db, email=email, fields=["email", "region", "role"])
    if err:
        # TODO: raise BusinessEception (force use async.)
        return res_err(msg=err)

    if res != None:
        return res_err(msg="email_registered")

    if sendby == "no_exist" and res == None:
        send_conform_code(email=email, confirm_code=confirm_code)
        return res_success(msg="email_sent")

    return res_err(msg="email_NOT_sent")


"""auth_service: signup
1. 去 S3 檢查 email 有沒註冊過，沒有 先寫入 email + version (auth gen)
2. 透過 private 解密出 pass
3. 產生 pass_salt
4. gen hash(pass + salt) = pass_hash
5. (delay rand msecs??) 檢查 version, 將 email + register_region 寫入 S3
6. gen packet_data 並寫入 DB
"""
@router.post("/signup")
def signup(
    email: EmailStr = Body(...),
    meta: str = Body(...),
    pubkey: str = Body(...),
    auth_db: Any = Depends(get_db),
    account_db: Any = Depends(get_db),
    obj_storage: Any = Depends(get_global_object_storage)
):
    # optimistic lock in S3?
    # 1. 去 S3 檢查 email 有沒註冊過
    email_info, err = obj_storage.find(bucket=email)
    if err:
        return res_err(msg=err)
    
    if email_info:
        return res_err(msg="registered", data=email_info)
    
    # 沒有註冊過 先寫入 email + version (auth gen)
    version = gen_random_string(6)
    version, err = obj_storage.init(bucket=email, version=version)
    if err:
        return res_err(msg=err)  # "email_registered" or "storage_upsert_error"

    # 2.~ 4.
    data = decrypt_meta(meta=meta, pubkey=pubkey)
    data["email"] = email
    region = data["region"]

    # 5. (delay rand msecs??) 檢查 version, 將 email + register_region 寫入 S3
    res, err = obj_storage.update(
        bucket=email, version=version, newdata={"region": region})
    if err:
        return res_err(msg=err)

    # 6. gen packet_data 並寫入 DB
    account_data = gen_account_data(data, "ft")
    # res = { aid, region, email, email2, is_active, role, role_id } = account_data
    res, err = auth_repo.create_account(
        auth_db=auth_db, account_db=account_db, email=email, data=account_data)
    if err:
        del_res, del_err = auth_repo.delete_account_by_email(
            auth_db=auth_db, account_db=account_db, email=email)
        if del_err:
            return res_err(msg=del_err)

        del_res, del_err = obj_storage.delete(bucket=email)
        if del_err:
            return res_err(msg=del_err)

        return res_err(msg=err)

    return res_success(data={
        "email": res["email"],
        "region": res["region"],
        "role": res["role"],
        "role_id": res["role_id"],
    })


@router.post("/login")
def login(
    email: EmailStr = Body(...),
    meta: str = Body(...),
    pubkey: str = Body(...),
    client_region: str = Body(...),
    auth_db: Any = Depends(get_db),
    account_db: Any = Depends(get_db),
    obj_storage: Any = Depends(get_global_object_storage)
):
    data = decrypt_meta(meta=meta, pubkey=pubkey)
    aid, err = auth_repo.authentication(
        db=auth_db, email=email, pw=data["pass"], match_password=match_password)
    if err == "error_password":
        return res_err(msg="error_password")

    if err == "not_registered":
        email_info, storage_err = obj_storage.find(bucket=email)
        if storage_err:
            log.error(f"/login fail, storage_err:{storage_err}")
            return res_err(msg=storage_err)
        
        elif email_info == None:
            return res_err(msg="not_registered")

        # email_info, S3 有，但是這地區的 DB 沒有，有可能在其他地區的 DB
        elif "region" in email_info and email_info["region"] != client_region:
            return res_err(data=email_info, msg="wrong_region")
 
        else:
            # email_info, S3 有:
            # 1. 有 region, 也顯示在該地區 -> S3有, DB沒有。
            # 2. 沒記錄 region
            return res_err(msg="register_fail")

    # unknow error
    if err:
        log.error(f"/login authentication fail, err:{err}")
        return res_err(msg=err)

    res, err = auth_repo.find_account(db=account_db, aid=aid)
    if err:
        log.error(f"/login find_account fail, err:{err}")
        return res_err(msg=err)
    
    
    res = filter_by_keys(res, ["email", "region", "role", "role_id"]) 
    return res_success(data=res)

@router.post('/reset_password')
def reset_password(
    payload: ResetPasswordPayload,
    auth_db: Any = Depends(get_db),
):
    err = auth_repo.reset_password(auth_db, payload.aid, payload.password1)
    if err != None:
        log.error(f"/reset_password fail, err:{err}")
        return res_err(msg=err)

    return res_success(msg='password modified')
