import json
import asyncio
import aioboto3
from botocore.exceptions import ClientError
from typing import Any, Callable
from ..resources.handlers import SQSResourceHandler
from ...models.event_vos import EventDetailVO
from ...configs.conf import (
    SQS_MAX_MESSAGES,
    SQS_WAIT_SECS,
)
import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class SqsMqAdapter:
    def __init__(self, sqs_rsc: SQSResourceHandler):
        self.sqs_rsc = sqs_rsc
        self.sqs_label = self.sqs_rsc.label
        self.ratio = 0.2
        self.delay = float(SQS_WAIT_SECS * self.ratio)
        self.loop = False

    async def publish_message(self, event: EventDetailVO):
        try:
            sqs_client = await self.sqs_rsc.access()
            message_body = json.dumps(event.dict())
            response = await sqs_client.send_message(
                QueueUrl=self.sqs_rsc.queue_url,
                MessageBody=message_body
            )

            log.info('SQS[%s]: msg is sent. msg ID: %s',
                     self.sqs_label, response['MessageId'])
            return response

        except Exception as e:
            log.error('SQS[%s]: Error sending message to SQS: %s',
                      self.sqs_label, str(e))
            raise e

    async def subscribe_messages(self, callee: Callable, **kwargs):
        if self.loop:
            log.info('SQS[%s]: subscribing messages ...', self.sqs_label)
            return

        sqs_client = await self.sqs_rsc.access()
        if self.loop:
            return
        
        self.loop = True
        while self.loop:
            await self.__receive_batch_messages(sqs_client, callee, **kwargs)
            await asyncio.sleep(1)  # Avoid busy waiting

    async def __receive_batch_messages(self, sqs_client: aioboto3.Session.client, callee: Callable, **kwargs):
        try:
            response = await sqs_client.receive_message(
                QueueUrl=self.sqs_rsc.queue_url,
                MaxNumberOfMessages=SQS_MAX_MESSAGES,
                WaitTimeSeconds=SQS_WAIT_SECS,
            )

            messages = response.get('Messages', [])
            for message in messages:
                log.info("SQS[%s]: Message received: %s",
                         self.sqs_label, message['Body'])
                request_body = json.loads(message['Body'])

                async def ack():
                    await sqs_client.delete_message(
                        QueueUrl=self.sqs_rsc.queue_url,
                        ReceiptHandle=message['ReceiptHandle'],
                    )

                # # ack: handled by callee
                # kwargs['ack'] = ack

                # main process
                await callee(request_body, **kwargs)
                await ack()

            # sleep 1 secs if there's no msgs
            if not messages:
                await asyncio.sleep(1)

        except ClientError as e:
            log.error('SQS[%s]: Error receiving messages: %s', self.sqs_label, str(e))
            await asyncio.sleep(self.delay)
            self.__exponential_backoff()
            if self.sqs_rsc.timeout():
                await self.sqs_rsc.access()
                self.loop = False
                log.info('SQS[%s]: break loop due to ClientError ...',
                         self.sqs_label)

        except Exception as e:
            log.error('SQS[%s]: Unexpected error: %s', self.sqs_label, str(e))
            await asyncio.sleep(self.delay)
            self.__exponential_backoff()
            if self.sqs_rsc.timeout():
                await self.sqs_rsc.access()
                self.loop = False
                log.info('SQS[%s]: break loop due to Exception ...',
                         self.sqs_label)

    def __exponential_backoff(self):
        self.delay = float(self.delay * (1 + self.ratio))
