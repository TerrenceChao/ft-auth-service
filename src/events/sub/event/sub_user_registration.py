from ....configs.conf import MAX_RETRY
from ....configs.constants import SubEventStatus
from ....models.event_vos import *
from ....models.auth_value_objects import *
from ....configs.adapters import *
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


# no testable
async def subscribe_user_registration(event: SubEventDetailVO):
    try:
        event.subscribed()
        log.info('subscribe_user_registration: %s, status: %s',
                 event.dict(), event.status.value)
        signup_vo = SignupVO.parse_obj(event.metadata)

        # main logic
        await auth_svc.duplicate_account_by_registered_region(
            signup_vo.auth,
            signup_vo.account,
            auth_db,
            account_db,
        )
        event.completed()
        await event_repo.append_sub_event_log(event)
        log.info('subscribe_user_registration and create signup data success %s, status: %s',
                 signup_vo.dict(), event.status.value)
        await event.call_ack()

    except Exception as e:
        if event.status == SubEventStatus.COMPLETED:
            log.warning('duplicate_account success but append log fail. event: %s',
                        event.dict())
            await event.call_ack()
            await alert_svc.exception_alert('[sub] event log writing fail.', e)
            return


        # dealing with the real sub-event retry process
        log.error('subscribe_user_registration error: %s', e)
        event.need_retry()
        if event.retry > MAX_RETRY:
            await alert_svc.exceed_retry_alert('retry event exceeds the max retry', event.retry)
            return

        try:
            await event_repo.append_sub_event_log(event)

            # publish to dead letter queue & retry
            await failed_subscribed_events_dlq.publish_message(event.payload())
            log.info('[subscribe_user_registration] send failed sub event to DLQ: %s, status: %s',
                     event.dict(), event.status.value)
            await event.call_ack()

        except Exception as e1:
            await alert_svc.exception_alert('An error occurred during retry', e1)
