import json
import asyncio
import aioboto3
import aioboto3.session
from botocore.exceptions import ClientError
from typing import Any, Callable

from ...configs.conf import (
    SQS_P_QUEUE_URL,
    SQS_S_QUEUE_URL,
    SQS_MAX_MESSAGES,
    SQS_WAIT_SECS,
)
from ...models.event_vos import EventDetailVO
import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


RETRY_PUB = 'retry_pub_events'
RETRY_SUB = 'retry_sub_events'

RETRY_TYPES = {
    RETRY_PUB: SQS_P_QUEUE_URL,
    RETRY_SUB: SQS_S_QUEUE_URL,
}
DELAY = float(SQS_WAIT_SECS * 0.2)


# TODO: to be deprecated

async def send_message(retry_type: str, event: EventDetailVO):
    async with aioboto3.Session().client('sqs') as sqs_client:

        # TODO: 配置或自定義重試機制
        try:
            message_body = json.dumps(event.dict())
            response = await sqs_client.send_message(
                QueueUrl=RETRY_TYPES[retry_type],
                MessageBody=message_body
            )
            log.info(type(response))
            # log.info(f'msg is sent to SQS. msg ID: {response['MessageId']}')
            return response

        except Exception as e:
            log.error(f'Error sending message to SQS: {str(e)}')
            raise e
        
        # finally:
        #     sqs_client.access()


async def receive_batch_messages(sqs_client: any, retry_type: str, callee: Callable, **kwargs):
    try:
        response = await sqs_client.receive_message(
            QueueUrl=RETRY_TYPES[retry_type],
            MaxNumberOfMessages=SQS_MAX_MESSAGES,
            WaitTimeSeconds=SQS_WAIT_SECS,
        )

        messages = response.get('Messages', [])
        for message in messages:
            log.info("SQS Message received: %s", message['Body'])
            request_body = json.loads(message['Body'])

            # main process
            # callee(f'{json.dumps(message)}')

            print(type(request_body))
            await callee(request_body)
            

            await sqs_client.delete_message(
                QueueUrl=RETRY_TYPES[retry_type],
                ReceiptHandle=message['ReceiptHandle'],
            )

        # sleep 1 secs if there's no msgs
        if not messages:
            await asyncio.sleep(1)

    except ClientError as e:
        log.error(f'Error receiving messages: {e}')
        await asyncio.sleep(DELAY)

    except Exception as e:
        log.error(f'Unexpected error: {e}')
        await asyncio.sleep(DELAY)


async def polling_messages(retry_type: str, callee: Callable, **kwargs):
    async with aioboto3.Session().client('sqs') as sqs_client:
        while True:
            await receive_batch_messages(sqs_client, retry_type, callee, **kwargs)
            await asyncio.sleep(1)  # Avoid busy waiting
