from ....configs.conf import MAX_RETRY
from ....models.event_vos import PubEventDetailVO
from ....infra.mq.event_bus import (
    publish_to_event_bus as publish_event_to_remote_regions,
)
from ....infra.mq.sqs import (
    RETRY_PUB,
    send_message as publish_event_to_dlq,
)
from ....configs.adapters import (
    event_repo,
    alert_svc,
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
        await publish_event_to_remote_regions(event.payload())
        event.published()
        await event_repo.append_pub_event_log(event)
        log.info('publish_remote_event: %s, status: %s',
                 event.dict(), event.status.value)

    except Exception as e:
        log.error('publish_remote_event error: %s', e)
        event.need_retry()
        if event.retry >= MAX_RETRY:
            await alert_svc.exceed_retry_alert('retry event exceeds the max retry', event.retry)
            return

        try:
            await event_repo.append_pub_event_log(event)

            # publish to dead letter queue & retry
            await publish_event_to_dlq(RETRY_PUB, event.payload())
            log.info('[publish_remote_event] send failed pub event to DLQ: %s, status: %s',
                     event.dict(), event.status.value)
        except Exception as e1:
            await alert_svc.exception_alert('An error occurred during retry', e1)
