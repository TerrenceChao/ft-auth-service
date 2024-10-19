import json
import aioboto3
from ...configs.conf import (
    LOCAL_REGION,
    EVENT_BUS_NAME,
    EVENT_SOURCE,
    EVENT_DETAIL_TYPE,
)
from ...models.event_vos import EventDetailVO
from ..utils.time_util import current_utc_time

import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

# TODO: to be deprecated

async def publish_to_event_bus(event: EventDetailVO):
    async with aioboto3.Session().client('events') as events_client:
        
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
            # 'Resources': [],
            # 'Time': current_utc_time(),
        }
        
        response = await events_client.put_events(Entries=[entry])
        log.info('Event sent: %s', json.dumps(response))