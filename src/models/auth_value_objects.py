from pydantic import BaseModel, EmailStr
from typing import Any, Type
from .event_vos import PubEventDetailVO
from ..configs.constants import *
from ..infra.db.nosql.auth_schemas import FTAuth, Account
from ..infra.utils.auth_util import gen_snowflake_id


class AccountVO(BaseModel):
    email: EmailStr
    region: str
    role: str
    role_id: int
    created_at: int


# 模擬 signup 當下註冊時的運作
class SignupVO(BaseModel):
    auth: FTAuth
    account: Account

    @classmethod
    def parse_obj(cls: Type['SignupVO'], obj: Any) -> 'SignupVO':
        obj = super().parse_obj(obj)
        obj.auth = FTAuth.parse_obj(obj.auth)
        obj.account = Account.parse_obj(obj.account)
        return obj


    def pub_event(self) -> (PubEventDetailVO):
        return PubEventDetailVO(
            event_id=gen_snowflake_id(),
            event_type=BusinessEventType.USER_REGISTRATION.value,
            metadata={
                'auth': self.auth.dict(),
                'account': self.account.dict(),
            },
            status=PubEventStatus.READY,
        )

    
    # filter sensitive data
    def to_account(self):
        account_vo = self.account
        account_vo.email2 = None
        return account_vo


class UpdatePasswordDTO(BaseModel):
    email: EmailStr
    pass_hash: str
    pass_salt: str

    def pub_event(self) -> (PubEventDetailVO):
        return PubEventDetailVO(
            event_id=gen_snowflake_id(),
            event_type=BusinessEventType.UPDATE_PASSWORD.value,
            metadata={
                'password_dto': self.dict(),
            },
            status=PubEventStatus.READY,
        )
