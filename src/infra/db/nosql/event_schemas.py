import json
from typing import Dict, Any
from pydantic import BaseModel
from .public_schemas import BaseEntity
from ...utils.auth_util import gen_snowflake_id
from ...utils.time_util import gen_timestamp


class EventEntity(BaseEntity):
    event_id: int   # partition key
    event_type: str
    metadata: Dict[Any, Any]
    status: str
    retry: int = 0



class EventLogEntity(BaseModel):
    log_id: int = gen_snowflake_id() # sort key
    event_id: int   # partition key
    event_type: str
    details: Dict[Any, Any]
    status: str
    retry: int = 0
    timestamp: int = gen_timestamp()

    @staticmethod
    def parse_event_entity(event: EventEntity) -> 'EventLogEntity':
        return EventLogEntity(
            log_id=gen_snowflake_id(),
            event_id=event.event_id,
            event_type=event.event_type,
            details=event.metadata,
            status=event.status,
            retry=event.retry,
            timestamp=gen_timestamp(),
        )
