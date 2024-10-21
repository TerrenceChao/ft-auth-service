from ....configs.conf import MAX_RETRY
from ....configs.constants import PubEventStatus
from ....models.event_vos import PubEventDetailVO
from ....configs.adapters import (
    event_bus_adapter as event_bus,
    event_repo,
    alert_svc,
    failed_publish_events_dlq,
)
import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


'''
- publish event to EventBus 
- append event log (published)
    - if publish fail
        - append event log (failed) 
        - publish event to DeadLetterQueue (DLQ) & retry
'''

# no testable


async def publish_remote_event(event: PubEventDetailVO):
    try:
        event.ready()
        log.info('publish_remote_event: %s, status: %s',
                 event.dict(), event.status.value)
        await event_bus.publish_message(event.payload())
        event.published()
        await event_repo.append_pub_event_log(event)
        log.info('publish_remote_event: %s, status: %s',
                 event.dict(), event.status.value)

    except Exception as e:
        if event.status == PubEventStatus.PUBLISHED:
            log.warning('publish success but append log fail. event: %s',
                        event.dict())
            await alert_svc.exception_alert('[pub] event log writing fail.', e)
            return


        # dealing with the real pub-event retry process
        log.error('publish_remote_event error: %s', e)
        event.need_retry()
        if event.retry > MAX_RETRY:
            await alert_svc.exceed_retry_alert('retry event exceeds the max retry', event.retry)
            return

        try:
            await event_repo.append_pub_event_log(event)

            # publish [failed pub event] to dead letter queue
            await failed_publish_events_dlq.publish_message(event.payload())
            log.info('[publish_remote_event] send failed pub event to DLQ: %s, status: %s',
                     event.dict(), event.status.value)
        except Exception as e1:
            await alert_svc.exception_alert('An error occurred during retry', e1)
