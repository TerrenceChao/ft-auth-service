from typing import Any
from pydantic import EmailStr
from ..repositories.auth_repository import IAuthRepository
from ..models.auth_value_objects import AccountVO
from ..models.email_value_objects import EmailAuthVO
from ..infra.client.email import Email
from ..configs.exceptions import *
import logging as log

log.basicConfig(filemode='w', level=log.INFO)


class EmailService:
    def __init__(self, auth_repo: IAuthRepository, email: Email):
        self.auth_repo = auth_repo
        self.email = email
        self.__cls_name = self.__class__.__name__

    def __find_account(self, account_db: Any, role_id: str) -> (AccountVO):
        res = self.auth_repo.find_account_by_role_id(
            db=account_db, role_id=role_id)
        if res is None:
            raise NotFoundException(msg='account_not_found')

        return AccountVO.parse_obj(res)

    def __get_recipient_email(
        self,
        account_db: Any,
        payload: EmailAuthVO
    ) -> (EmailStr):
        if payload.recipient_email != None and payload.recipient_email != '':
            return payload.recipient_email

        recipient = self.__find_account(
            account_db=account_db,
            role_id=payload.recipient_id,
        )
        if recipient.role != payload.recipient_role:
            raise ForbiddenException(msg='recipient_role_mismatch')

        return recipient.email

    '''
    - get sender's email(registration email) by sender_id
    - get recipient's email by recipient_id
    - send email with body sender's email 
    '''
    async def send_contact(
        self,
        account_db: Any,
        payload: EmailAuthVO
    ):
        log.debug(f'send contact, payload:{payload}')
        try:
            sender = self.__find_account(
                account_db=account_db,
                role_id=payload.sender_id,
            )
            if sender.role != payload.sender_role:
                raise ForbiddenException(msg='sender_role_mismatch')

            recipient_email = self.__get_recipient_email(account_db, payload)

            await self.email.send_contact(
                recipient=recipient_email,
                subject=payload.subject,
                body=f'{payload.body}\n\nfrom: {sender.email}',
            )

        except Exception as e:
            log.error(f'{self.__cls_name} - send_contact: {e}')
            raise_http_exception(e)
