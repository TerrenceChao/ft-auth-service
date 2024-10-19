from ....services.event_service import *
from ....models.event_vos import *
from ....models.auth_value_objects import *
from ....configs.adapters import *
from ....infra.mq.sqs import (
    RETRY_SUB,
    send_message as publish_event_to_dlq,  # no testable
)


# no testable
async def subscribe_user_registration(event: SubEventDetailVO):
    try:
        event.subscribed()
        log.info('subscribe_user_registration: %s, status: %s',
                 event.dict(), event.status.value)
        signup_vo = SignupVO.parse_obj(event.metadata)
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

    except Exception as e:
        log.error('subscribe_user_registration error: %s', e)
        event.need_retry()
        if event.retry >= MAX_RETRY:
            await alert_svc.exceed_retry_alert('retry event exceeds the max retry', event.retry)
            return

        try:
            await event_repo.append_sub_event_log(event)

            # publish to dead letter queue & retry
            await publish_event_to_dlq(RETRY_SUB, event.payload())
            log.info('[subscribe_user_registration] send failed sub event to DLQ: %s, status: %s',
                     event.dict(), event.status.value)
        except Exception as e1:
            await alert_svc.exception_alert('An error occurred during retry', e1)
