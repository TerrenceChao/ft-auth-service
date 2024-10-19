from fastapi import BackgroundTasks
from typing import Any, Callable
from ..configs.conf import MAX_RETRY
from ..configs.exceptions import ServerException
from ..models.event_vos import PubEventDetailVO
from ..repositories.event_repository import IEventRepository
import logging


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

# TODO: to be deprecated

class EventService:
    def __init__(self, repo: IEventRepository):
        self.repo = repo

    async def exceed_retry_alert(self, max_retry: int):
        # slack, TG, ... alert
        raise ServerException(msg=f'event exceeds the max retry: {max_retry}')

    async def retry_exception(self, e: Any):
        # slack, TG, ... alert
        log.error(f"An error occurred during retry: {str(e)}")
        raise ServerException(msg=f'retry error: {str(e)}')


















def publish_remote_event_task(bg_task: BackgroundTasks, svc: EventService, db: Any, event: PubEventDetailVO):
    bg_task.add_task(publish_event, svc=svc, db=db, event=event)



'''
- X) write event log (ready)
- publish event to EventBus
    - if publish fail
        - write event log (pub fail) 
        - publish event to DeadLetterQueue (DLQ)
'''
async def publish_event(svc: EventService, db: Any, event: PubEventDetailVO):
    try:
        event.ready()
        # 不用 PubEventStatus:READY 的情況下，先發送事件再寫 log
        # await svc.repo.append_pub_event_log(db, event)
        log.info('publish_event: %s, status: %s', event.dict(), event.status.value)
        await svc.publish_event_to_event_bus(event.payload())
        event.published()
        await svc.repo.append_pub_event_log(db, event)
        log.info('publish_event: %s, status: %s', event.dict(), event.status.value)

    except Exception as e:
        log.error('publish_event error: %s', e)
        event.need_retry()
        if event.retry >= MAX_RETRY:
            await svc.exceed_retry_alert(event.retry)

        try:
            # 已經建立過 event log (假設 DB 沒壞的話)
            await svc.repo.update_pub_event_log_status(db, event)
            await svc.publish_event_to_dlq(event.payload())
            log.info('publish_event: %s, status: %s', event.dict(), event.status.value)
        except Exception as e1:
            await svc.retry_exception(e1)



'''
- X) update event log (ready)
- publish event to EventBus
    - if publish fail
        - write event log (pub fail) 
        - publish event to DeadLetterQueue (DLQ)
'''
async def retry_publish_event(svc: EventService, db: Any, event: PubEventDetailVO):
    try:
        event.ready()
        # 不用 PubEventStatus:READY 的情況下，先發送事件再寫 log
        # event.status = PubEventStatus.READY
        # await svc.repo.update_pub_event_log_status(db, event)
        log.info('publish_event: %s, status: %s', event.dict(), event.status.value)
        await svc.publish_event_to_event_bus(event.payload())
        event.published()
        await svc.repo.update_pub_event_log_status(db, event)
        log.info('publish_event: %s, status: %s', event.dict(), event.status.value)

    except Exception as e:
        log.error('publish_event error: %s', e)
        event.need_retry()
        if event.retry >= MAX_RETRY:
            await svc.exceed_retry_alert(event.retry)

        try:
            await svc.repo.update_pub_event_log_status(db, event)

            # publish to dead letter queue
            await svc.publish_event_to_dlq(event.payload())
            log.info('publish_event: %s, status: %s', event.dict(), event.status.value)
        except Exception as e1:
            await svc.retry_exception(e1)
