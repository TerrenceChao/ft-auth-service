from typing import Any
from fastapi import BackgroundTasks
from ._base_publish import publish_remote_event
from ....models import event_vos as evt
import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


async def publish_remote_user_registration(signup_data: evt.SignupVO):
    pub_event: evt.PubEventDetailVO = signup_data.pub_event()
    await publish_remote_event(pub_event)


async def publish_remote_user_login(user_data: Any):
    # TODO: Preprocessing ...
    # await publish_remote_event(pub_event)
    log.info('TODO: implement publish_remote_user_login ..')


async def publish_remote_update_passowrd(sensitive_data: Any):
    # TODO: Preprocessing ...
    # await publish_remote_event(pub_event)
    log.info('TODO: implement publish_remote_update_passowrd ..')




#####################
# background tasks
#####################

def publish_remote_user_registration_task(bg_task: BackgroundTasks, signup_data: evt.SignupVO):
    log.info('background processing publish_remote_user_registration ...')
    bg_task.add_task(publish_remote_user_registration, signup_data=signup_data)


def publish_remote_user_login_task(bg_task: BackgroundTasks, data: Any):
    log.info('background processing publish_remote_user_login ...')
    bg_task.add_task(publish_remote_user_login, user_data=data)


def publish_remote_update_passowrd_task(bg_task: BackgroundTasks, data: Any):
    log.info('background processing publish_remote_update_passowrd ...')
    bg_task.add_task(publish_remote_update_passowrd, sensitive_data=data)
