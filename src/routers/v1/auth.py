from typing import Any, Dict
from fastapi import APIRouter, Depends, Body, status, BackgroundTasks
from pydantic import EmailStr
from ..req.auth_validation import decrypt_meta_for_signup, decrypt_meta, ResetPasswordPayload
from ..res.response import post_success, res_success
from ...services.auth_service import AuthService
from ...configs.adapters import *
from ...events.pub.event.publish_remote_events import (
    publish_remote_user_registration_task,
    # publish_remote_user_login_task,
    # publish_remote_update_passowrd_task,
)
from ...infra.utils.auth_util import get_public_key
from ...infra.db.nosql.auth_repository import AuthRepository
import logging as log

log.basicConfig(filemode='w', level=log.INFO)


auth_service = AuthService(
    auth_repo=AuthRepository(),
    obj_storage=global_object_storage,
    email=email_client,
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


@router.post('/sendcode/email', status_code=status.HTTP_201_CREATED)
async def send_conform_code_by_email(
    email: EmailStr = Body(...),
    confirm_code: str = Body(...),
    sendby: str = Body(...),
    # auth_db: Any = Depends(get_db),
    # account_db: Any = Depends(get_db)
):
    res = await auth_service.send_conform_code_by_email(
        email=email,
        confirm_code=confirm_code,
        sendby=sendby,
        auth_db=auth_db,
        account_db=account_db
    )

    return post_success(data=res)


@router.post('/signup', status_code=status.HTTP_201_CREATED)
async def signup(
    bg_task: BackgroundTasks,
    email: EmailStr = Body(...),
    # meta ex: "{\"role\":\"teacher\",\"pass\":\"secret\"}"
    data: Dict = Depends(decrypt_meta_for_signup),
    # auth_db: Any = Depends(get_db),
    # account_db: Any = Depends(get_db),
):
    signup_data = await auth_service.signup(
        email=email,
        data=data,
        auth_db=auth_db,
        account_db=account_db,
    )
    # publidh event & duplicate signup data to remote regions
    publish_remote_user_registration_task(bg_task=bg_task, signup_data=signup_data)

    return post_success(data=signup_data.to_account())


@router.post('/login')
async def login(
    email: EmailStr = Body(...),
    # meta ex: "{\"pass\":\"secret\"}"
    data: Dict = Depends(decrypt_meta),
    current_region: str = Body(...),
    # auth_db: Any = Depends(get_db),
    # account_db: Any = Depends(get_db),
):
    res = await auth_service.login(
        email=email,
        data=data,
        current_region=current_region,
        auth_db=auth_db,
        account_db=account_db,
    )

    return post_success(data=res)


@router.put('/password/update')
async def update_password(
    payload: ResetPasswordPayload,
    # auth_db: Any = Depends(get_db),
):
    await auth_service.update_password(
        auth_db, 
        payload.register_email, 
        payload.password1, 
        payload.origin_password
    )
    return res_success(msg='password modified')


@router.get('/password/reset/email')
async def send_reset_password_confirm_email(
    email: EmailStr,
    # auth_db: Any = Depends(get_db),
    # account_db: Any = Depends(get_db),
):
    verify_token = await auth_service.send_reset_password_confirm_email(auth_db, account_db, email)
    return res_success(msg='password modified', data={'token': verify_token})
