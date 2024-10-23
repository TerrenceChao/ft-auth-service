from ....configs.conf import MAX_RETRY
from ....configs.constants import SubEventStatus
from ....models.event_vos import *
from ....models.auth_value_objects import *
from ....configs.adapters import *
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


# no testable
async def subscribe_update_password(event: SubEventDetailVO):
    try:
        event.subscribed()
        log.info('subscribe_update_password: %s, status: %s',
                 event.dict(), event.status.value)
        pass_params = UpdatePasswordDTO.parse_obj(event.metadata)

        # main logic
        await auth_svc.update_password_by_remote_event(
            db=auth_db,
            params=pass_params,
        )
        event.completed()
        await event_repo.append_sub_event_log(event)
        log.info('subscribe_update_password and update password success %s, status: %s',
                 pass_params.dict(), event.status.value)
        await event.call_ack()

    except Exception as e:
        if event.status == SubEventStatus.COMPLETED:
            log.warning('update password success but append log fail. event: %s',
                        event.dict())
            await event.call_ack()
            await alert_svc.exception_alert('[sub] event log writing fail.', e)
            return

        # dealing with the real sub-event retry process
        log.error('subscribe_update_password error: %s', e)
        event.need_retry()
        if event.retry > MAX_RETRY:
            await alert_svc.exceed_retry_alert('retry event exceeds the max retry', event.retry)
            return

        try:
            await event_repo.append_sub_event_log(event)

            # publish to dead letter queue & retry
            await failed_subscribed_events_dlq.publish_message(event.payload())
            log.info('[subscribe_update_password] send failed sub event to DLQ: %s, status: %s',
                     event.dict(), event.status.value)
            await event.call_ack()

        except Exception as e1:
            await alert_svc.exception_alert('An error occurred during retry', e1)
