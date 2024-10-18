from typing import Any, Dict
from fastapi import APIRouter, \
    Request, Depends, Header, Path, Query, Body
from ...models.email_value_objects import EmailAuthVO
from ..res.response import res_success
from ...services.email_service import EmailService
from ...configs.adapters import *
from ...infra.db.nosql.auth_repository import AuthRepository
import logging as log

log.basicConfig(filemode='w', level=log.INFO)


_email_service = EmailService(
    auth_repo=AuthRepository(),
    email=email_client,
)


router = APIRouter(
    prefix='/auth-nosql',
    tags=['notify'],
    responses={404: {'description': 'Not found'}},
)


@router.post('/notify/email')
async def send_contact_by_email(
    payload: EmailAuthVO = Body(...),
    # account_db: Any = Depends(get_db)
):
    await _email_service.send_contact(
        account_db,
        payload
    )
    return res_success(msg='email_sent')
