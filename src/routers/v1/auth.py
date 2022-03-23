from atexit import register
import json
from typing import List, Dict, Any
from unicodedata import name
from fastapi import APIRouter, \
    Request, Depends, \
    Cookie, Header, Path, Query, Body, Form, \
    File, UploadFile, status, \
    HTTPException
from ..res.response import res_success, res_err
from ...common.auth_util import get_public_key, decrypt_meta, \
    gen_account_data, \
    hash_func, gen_token
from ...common.object_storage import init_global_storage, \
    update_global_storage, \
    delete_global_storage, \
    find_global_storage
from ...common.email_util import send_conform_code
from ...db.nosql.database import get_db
from ...db.nosql import schemas, auth_repository
from ..exceptions import BusinessEception


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
    email: str = Body(...),
    confirm_code: str = Body(...),
    sendby: str = Body(...),
    auth_db: Any = Depends(get_db),
    account_db: Any = Depends(get_db)
):

    res, err = auth_repo.get_account_by_email(
        auth_db=auth_db, account_db=account_db, email=email, fields=["email", "region", "role"])
    if err != None:
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
7. gen JWT
"""


@router.post("/signup")
def signup(
    email: str = Body(...),
    meta: str = Body(...),
    pubkey: str = Body(...),
    auth_db: Any = Depends(get_db),
    account_db: Any = Depends(get_db)
):
    # optimistic lock in S3?
    # 1. 去 S3 檢查 email 有沒註冊過，沒有 先寫入 email + version (auth gen)
    version, err = init_global_storage(bucket=email, data=email)
    if err != None:
        return res_err(msg=err)  # "email_registered" or "storage_upsert_error"

    # 2.~ 4.
    data = decrypt_meta(meta=meta, pubkey=pubkey)
    data["email"] = email
    region = data["region"]

    # 5. (delay rand msecs??) 檢查 version, 將 email + register_region 寫入 S3
    res, err = update_global_storage(
        bucket=email, olddata=f"{email}_{version}", newdata={"region": region})
    if err != None:
        return res_err(msg=err)

    # 6. gen packet_data 並寫入 DB
    account_data = gen_account_data(data)
    # res = { aid, region, email, email2, is_active, role, role_id } = account_data
    res, err = auth_repo.create_account(
        auth_db=auth_db, account_db=account_db, email=email, data=account_data)
    if err != None:
        del_res, del_err = auth_repo.delete_account_by_email(
            auth_db=auth_db, account_db=account_db, email=email)
        if del_err != None:
            return res_err(msg=del_err)

        del_res, del_err = delete_global_storage(bucket=email)
        if del_err != None:
            return res_err(msg=del_err)

        return res_err(msg=err)

    # 7. gen JWT
    token = gen_token(data=account_data)
    return res_success(data={
        "email": res["email"],
        "region": res["region"],
        "role": res["role"],
        "role_id": res["role_id"],
        "token": token
    })


@router.post("/login")
def login(
    email: str = Body(...),
    meta: str = Body(...),
    pubkey: str = Body(...),
    auth_db: Any = Depends(get_db),
    account_db: Any = Depends(get_db)
):
    data = decrypt_meta(meta=meta, pubkey=pubkey)
    print(data, type(data))
    aid, err = auth_repo.authentication(
        db=auth_db, email=email, pw=data["pass"], hash_func=hash_func)
    if err == "error_password":
        return res_err(msg="error_password")

    if err == "not_registered":
        email_info, storage_err = find_global_storage(bucket=email)
        if email_info == None:
            return res_err(msg="not_registered")

        else:
            # log email_info, S3 有但是 DB 沒有!?!?!?
            return res_err(msg="register_fail")

    # unknow error
    if err != None:
        return res_err(msg=err)

    res, err = auth_repo.find_account(db=account_db, aid=aid)
    if err != None:
        return res_err(msg=err)

    token = gen_token(data=res)
    return res_success(data={
        "email": res["email"],
        "region": res["region"],
        "role": res["role"],
        "role_id": res["role_id"],
        "token": token
    })
