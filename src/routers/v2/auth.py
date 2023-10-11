# TODO: 在這裡 (src/routers/v2/auth.py) 新增 routers 做 API:
# [1]. Update password
# [2]. Close/disable account
# [3]. Forgot password
#
# 用一般的三層式寫法: routers -> service -> repository
# 參考 src/routers/v1/auth.py, src/services/auth_service.py, src/db/nosql/auth_repository.py
from typing import Any
from fastapi import APIRouter, \
    Request, Depends, \
    Cookie, Header, Path, Query, Body, Form, \
    File, UploadFile, status, \
    HTTPException
from pydantic import EmailStr
from ..req.auth_validation import ResetPasswordPayload
from ..res.response import res_success, res_err
from ...services.auth_service import AuthService
from ...configs.database import get_db, get_client
from ...configs.s3 import get_s3_resource
from ...infra.utils.auth_util import get_public_key
from ...infra.db.nosql.auth_repository import AuthRepository
from ...infra.storage.global_object_storage import GlobalObjectStorage
from ...infra.apis.email import send_conform_code
import logging as log


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


@router.post('/update_password')
def update_password(
    payload: ResetPasswordPayload,
    auth_db: Any = Depends(get_db),
):
    auth_service.update_password(auth_db, payload.register_email, payload.password1, payload.origin_password)
    return res_success(msg='password modified')
