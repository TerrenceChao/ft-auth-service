import json
from typing import Dict
from ...configs.constants import BusinessEventType
from .event.sub_user_registration import *
from ..pub.event.publish_remote_events import *
import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


async def subscribe_event(handlers: Dict, event_type: str, event_detail: Dict, category: str):
    try:
        if not event_type in handlers:
            log.info('no event_type: %s in the handler', event_type)
            return

        sub_event = SubEventDetailVO.parse_obj(event_detail)
        await handlers[event_type](sub_event)

    except Exception as e:
        log.error('[%s]: subscribe_event error: %s', category, e.__str__())
        raise e


def get(event_detail: Dict, key: str):
    if not key in event_detail:
        log.error('%s is not in event_detail: \n%s',
                  key, json.dumps(event_detail))
        raise ServerException(f'{key} is not in event_detail')
    
    return event_detail[key]




# Subscribe EventBridge for remote events
class SubscribeRemoteEventManager:
    def __init__(self, handlers: Dict[str, Callable]):
        self.handlers = handlers

    async def subscribe_event(self, event_detail: Dict):
        if not len(self.handlers):
            log.info('no handler here')
            return
        
        event_type = get(event_detail, 'event_type')
        await subscribe_event(self.handlers, event_type, event_detail, 'Remote')


sub_remote_event_manager = SubscribeRemoteEventManager({
    BusinessEventType.USER_REGISTRATION.value: subscribe_user_registration,
    BusinessEventType.USER_LOGIN.value: None,  # TODO: pending...
    BusinessEventType.UPDATE_PASSWORD.value: None,  # TODO: pending...
})




# Subscribe SQS for retry failed publish events (DEAL LETTER QUEUE)
class RetryPublishEventManager:
    def __init__(self, handlers: Dict[str, Callable]):
        self.handlers = handlers

    async def subscribe_event(self, event_detail: Dict):
        if not len(self.handlers):
            log.info('no handler here')
            return
        
        event_type = get(event_detail, 'event_type')
        await subscribe_event(self.handlers, event_type, event_detail, 'Retry Failed Pub Events')


retry_pub_event_manager = RetryPublishEventManager({
    # retry failed publish events
    BusinessEventType.USER_REGISTRATION.value: publish_remote_user_registration,
    BusinessEventType.USER_LOGIN.value: publish_remote_user_login,    # TODO: pending...
    BusinessEventType.UPDATE_PASSWORD.value: publish_remote_update_passowrd,  # TODO: pending...
})




# Subscribe SQS for retry failed subscribe events (DEAL LETTER QUEUE)
class RetrySubscribeEventManager:
    def __init__(self, handlers: Dict[str, Callable]):
        self.handlers = handlers

    async def subscribe_event(self, event_detail: Dict):
        if not len(self.handlers):
            log.info('no handler here')
            return

        event_type = get(event_detail, 'event_type')
        await subscribe_event(self.handlers, event_type, event_detail, 'Retry Failed Sub Events')


retry_sub_event_manager = RetrySubscribeEventManager({
    # retry failed subscribed events
    BusinessEventType.USER_REGISTRATION.value: subscribe_user_registration,
    # BusinessEventType.USER_LOGIN.value: None,     # TODO: pending...
    # BusinessEventType.UPDATE_PASSWORD.value: None,    # TODO: pending...
})
