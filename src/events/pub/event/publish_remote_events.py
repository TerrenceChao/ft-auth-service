from typing import Any
from fastapi import BackgroundTasks
from ._base_publish import publish_remote_event
from ....models.event_vos import PubEventDetailVO
from ....models.auth_value_objects import (
    SignupVO,
    UpdatePasswordDTO,
)
import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


async def publish_remote_user_registration(signup_data: SignupVO):
    log.info('publishing remote_user_registration event ..')
    pub_event: PubEventDetailVO = signup_data.pub_event()
    await publish_remote_event(pub_event)


async def publish_remote_user_login(user_data: Any):
    # TODO: Preprocessing ...
    log.info('TODO: implement publish_remote_user_login ..')
    # await publish_remote_event(pub_event)


async def publish_remote_update_passowrd(sensitive_data: UpdatePasswordDTO):
    log.info('publishing remote_update_passowrd event ..')
    pub_event: PubEventDetailVO = sensitive_data.pub_event()
    await publish_remote_event(pub_event)




#####################
# background tasks
#####################

def publish_remote_user_registration_task(bg_task: BackgroundTasks, signup_data: SignupVO):
    log.info('background processing publish_remote_user_registration ...')
    bg_task.add_task(publish_remote_user_registration, signup_data=signup_data)


def publish_remote_user_login_task(bg_task: BackgroundTasks, data: Any):
    log.info('background processing publish_remote_user_login ...')
    bg_task.add_task(publish_remote_user_login, user_data=data)


def publish_remote_update_passowrd_task(bg_task: BackgroundTasks, sensitive_data: UpdatePasswordDTO):
    log.info('background processing publish_remote_update_passowrd ...')
    bg_task.add_task(publish_remote_update_passowrd, sensitive_data=sensitive_data)
