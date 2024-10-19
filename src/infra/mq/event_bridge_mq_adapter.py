import json
from typing import Callable
from ..resources.handlers import EventBridgeResourceHandler
from ...models.event_vos import EventDetailVO
from ...configs.conf import (
    LOCAL_REGION,
    EVENT_BUS_NAME,
    EVENT_SOURCE,
    EVENT_DETAIL_TYPE,
)
from ..utils.time_util import current_utc_time
import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

class EventBridgeMqAdapter:
    def __init__(self, event_bus_rsc: EventBridgeResourceHandler):
        self.event_bus_rsc = event_bus_rsc

    async def publish_message(self, event: EventDetailVO):
        events_client = await  self.event_bus_rsc.access()
            
        # TODO: 配置或自定義重試機制
        event_dict = event.dict()
        event_dict.update({
            'region': LOCAL_REGION,
        })
        entry = {
            'EventBusName': EVENT_BUS_NAME,  # 使用默認事件總線
            'Source': EVENT_SOURCE,
            'DetailType': EVENT_DETAIL_TYPE,
            'Detail': json.dumps(event_dict),
            'Resources': [],
            'Time': current_utc_time(),
        }
        
        response = await events_client.put_events(Entries=[entry])
        log.info('Event sent: %s', json.dumps(response))

    async def subscribe_messages(self, callee: Callable, **kwargs):
        pass