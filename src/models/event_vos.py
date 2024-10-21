from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, List, Any, Type, Callable
from ..configs.constants import *
from ..infra.db.nosql.auth_schemas import FTAuth, Account
from ..infra.utils.auth_util import gen_snowflake_id


class EventDetailVO(BaseModel):
    event_id: int
    event_type: str
    metadata: Dict[Any, Any]
    retry: int = 0

    def payload(self) -> 'EventDetailVO':
        return EventDetailVO.parse_obj({
            'event_id': self.event_id,
            'event_type': self.event_type,
            'metadata': self.metadata,
            'retry': self.retry,
        })


class PubEventDetailVO(EventDetailVO):
    status: PubEventStatus = PubEventStatus.READY

    def ready(self) -> 'PubEventDetailVO':
        self.status = PubEventStatus.READY
        return self
    
    def published(self) -> 'PubEventDetailVO':
        self.status = PubEventStatus.PUBLISHED
        return self

    def need_retry(self) -> 'PubEventDetailVO':
        self.status = PubEventStatus.PUB_FAILED
        self.retry += 1
        return self
    
    def dict(self):
        original_dict = super().dict()
        original_dict['status'] = original_dict['status'].value  # 轉換 Enum 為其值
        return original_dict


class SubEventDetailVO(EventDetailVO):
    status: SubEventStatus = SubEventStatus.SUBSCRIBED
    ack: Optional[Callable] = None

    def subscribed(self) -> 'SubEventDetailVO':
        self.status = SubEventStatus.SUBSCRIBED
        return self
    
    def completed(self) -> 'SubEventDetailVO':
        self.status = SubEventStatus.COMPLETED
        return self

    def need_retry(self) -> 'SubEventDetailVO':
        self.status = SubEventStatus.SUB_FAILED
        self.retry += 1
        return self
    
    async def call_ack(self):
        if self.ack:
            await self.ack()
    
    def dict(self):
        original_dict = super().dict()
        original_dict['status'] = original_dict['status'].value  # 轉換 Enum 為其值
        return original_dict
