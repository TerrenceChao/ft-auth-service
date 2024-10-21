import json
from typing import Dict, Callable
from ...configs.constants import BusinessEventType
from ...configs.exceptions import ServerException
from ...models.event_vos import SubEventDetailVO
from .event import *
from ..pub.event.publish_remote_events import *
import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class SubscribeEventManager:
    def __init__(self, label: str, handlers: Dict[str, Callable]):
        self.label = label
        self.handlers = handlers

    async def subscribe_event(self, event_detail: Dict):
        if not len(self.handlers):
            log.info('[%s]: no handler here', self.label)
            return

        event_type = self.get(event_detail, 'event_type')
        await self.__subscribe_event(event_type, event_detail)

    async def __subscribe_event(self, event_type: str, event_detail: Dict):
        try:
            if not event_type in self.handlers:
                log.info('[%s]: no event_type: %s in the handler',
                         self.label, event_type)
                return

            sub_event = SubEventDetailVO.parse_obj(event_detail)
            await self.handlers[event_type](sub_event)

        except Exception as e:
            log.error('[%s]: subscribe_event error: %s',
                      self.label, e.__str__())
            raise e

    def get(self, event_detail: Dict, key: str):
        if not key in event_detail:
            log.error('[%s]: "%s" is not in event_detail: \n%s',
                      self.label, key, json.dumps(event_detail))
            raise ServerException(f'event_type: {key} is not in event_detail')

        return event_detail[key]


# Subscribe EventBridge from remote regions
sub_remote_event_manager = SubscribeEventManager(
    'Subscribe event bus from remote regions',
    {
        BusinessEventType.USER_REGISTRATION.value: subscribe_user_registration,
        # TODO: pending...
        # BusinessEventType.USER_LOGIN.value: None,
        BusinessEventType.UPDATE_PASSWORD.value: subscribe_update_password,
    })


# Subscribe SQS for retry failed subscribe events (DEAL LETTER QUEUE)
retry_sub_event_manager = SubscribeEventManager(
    'Subscribe msgs for retry failed subscribe events(DLQ)',
    {
        # retry failed subscribed events
        BusinessEventType.USER_REGISTRATION.value: subscribe_user_registration,
        # TODO: pending...
        # BusinessEventType.USER_LOGIN.value: None,
        BusinessEventType.UPDATE_PASSWORD.value: subscribe_update_password,
    })


# Subscribe SQS for retry failed publish events (DEAL LETTER QUEUE)
retry_pub_event_manager = SubscribeEventManager(
    'Subscribe msgs for retry failed publish events(DLQ)',
    {
        # retry failed publish events
        BusinessEventType.USER_REGISTRATION.value: publish_remote_user_registration,
        # TODO: pending...
        BusinessEventType.USER_LOGIN.value: publish_remote_user_login,
        # TODO: pending...
        BusinessEventType.UPDATE_PASSWORD.value: publish_remote_update_passowrd,
    })
