from typing import Any, Dict
from fastapi import APIRouter, \
    Request, Depends, Header, Path, Query, Body
from ...models.email_value_objects import EmailVO
from ..res.response import res_success
from ...services.email_service import EmailService
from ...configs.database import get_db
from ...infra.db.nosql.auth_repository import AuthRepository
from ...infra.apis.email import Email
import logging as log

log.basicConfig(filemode='w', level=log.INFO)


auth_repo = AuthRepository()
email = Email()
_email_service = EmailService(
    auth_repo=auth_repo,
    email=email,
)

router = APIRouter(
    prefix='/auth-nosql',
    tags=['notify'],
    responses={404: {'description': 'Not found'}},
)


@router.post('/notify/email')
async def send_contact_by_email(
    payload: EmailVO = Body(...),
    account_db: Any = Depends(get_db)
):
    await _email_service.send_contact(
        account_db,
        payload
    )
    return res_success(msg='email_sent')
