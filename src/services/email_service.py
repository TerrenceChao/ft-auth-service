from typing import Any
from ..repositories.auth_repository import IAuthRepository
from ..models.auth_value_objects import AccountVO
from ..models.email_value_objects import EmailVO
from ..infra.apis.email import Email
from ..configs.exceptions import *
import logging as log

log.basicConfig(filemode='w', level=log.INFO)


class EmailService:
    def __init__(self, auth_repo: IAuthRepository, email: Email):
        self.auth_repo = auth_repo
        self.email = email
        self.__cls_name = self.__class__.__name__

    def __find_account(self, account_db: Any, aid: str) -> (AccountVO):
        res = self.auth_repo.find_account(db=account_db, aid=aid)
        if res is None:
            raise NotFoundException(msg='account_not_found')

        return AccountVO.parse_obj(res)

    '''
    - get sender's email(registration email) by sender_id
    - get recipient's email by recipient_id
    - send email with body sender's email 
    '''
    async def send_contact(
        self,
        account_db: Any,
        payload: EmailVO
    ):
        log.debug(f'send contact, payload:{payload}')
        try:
            sender = self.__find_account(
                account_db=account_db,
                aid=payload.sender_id,
            )
            recipient = self.__find_account(
                account_db=account_db,
                aid=payload.recipient_id,
            )
            await self.email.send_contact(
                recipient=recipient.email,
                subject=payload.subject,
                body=f'{payload.body}\n\nfrom: {sender.email}',
            )

        except Exception as e:
            log.error(f'{self.__cls_name} - send_contact: {e}')
            raise ServerException(msg='send_contact error')
