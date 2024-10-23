from pydantic import BaseModel, EmailStr
from typing import Any, Type, Optional
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
            role_id=self.auth.role_id,
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
    role_id: Optional[int] = None

    def set_role_id(self, role_id: int):
        self.role_id = role_id
        return self

    def pub_event(self) -> (PubEventDetailVO):
        return PubEventDetailVO(
            event_id=gen_snowflake_id(),
            event_type=BusinessEventType.UPDATE_PASSWORD.value,
            role_id=self.role_id,   # TODO: 123 啥時給 role_id? 沒給就不能 publish
            metadata=self.dict(),
            status=PubEventStatus.READY,
        )
