import asyncio
import aioboto3
from botocore.config import Config
from ._resource import ResourceHandler
from ....configs.conf import (
    MQ_CONNECT_TIMEOUT,
    MQ_READ_TIMEOUT,
    MQ_MAX_ATTEMPTS,
)
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


mq_config = Config(
    connect_timeout=MQ_CONNECT_TIMEOUT,
    read_timeout=MQ_READ_TIMEOUT,
    retries={'max_attempts': MQ_MAX_ATTEMPTS}
)


class SQSResourceHandler(ResourceHandler):

    def __init__(self, session: aioboto3.Session, label: str, queue_url: str):
        super().__init__()
        self.max_timeout = MQ_CONNECT_TIMEOUT

        self.lock = asyncio.Lock()
        self.session = session
        self.label = label
        self.queue_url = queue_url
        self.sqs_client = None
        self.trigger_subscribe_messages = None

    def timeout(self) -> bool:
        return False

    async def initial(self):
        try:
            async with self.lock:
                if self.sqs_client is None:
                    async with self.session.client('sqs', config=mq_config) as sqs_client:
                        self.sqs_client = sqs_client
                        response = await self.sqs_client.get_queue_attributes(
                            QueueUrl=self.queue_url,
                            AttributeNames=['QueueArn']
                        )
                        log.info('Message Queue[SQS] Connection QueueArn: %s',
                                 response['Attributes']['QueueArn'])

        except Exception as e:
            log.error(e.__str__())
            async with self.lock:
                async with self.session.client('sqs', config=mq_config) as sqs_client:
                    self.sqs_client = sqs_client

    async def accessing(self, **kwargs):
        async with self.lock:
            if self.sqs_client is None:
                await self.initial()

            # assign trigger_subscribe_messages function
            trigger_subscribe_messages = kwargs.get(
                'trigger_subscription', None)
            if trigger_subscribe_messages:
                self.trigger_subscribe_messages = trigger_subscribe_messages

            return self.sqs_client

    # Regular activation to maintain connections and connection pools
    async def probe(self):
        try:
            response = await self.sqs_client.get_queue_attributes(
                QueueUrl=self.queue_url,
                AttributeNames=['QueueArn'],
            )
            log.info('Message Queue[SQS] Connection HTTPStatusCode: %s',
                     response['ResponseMetadata']['HTTPStatusCode'])
        except Exception as e:
            log.error(f'Message Queue[SQS] Connection Error: %s', e.__str__())
            await self.initial()

        finally:
            if self.trigger_subscribe_messages:
                log.info(
                    'Probing Message Queue[SQS]: trigger_subscribe_messages!')
                await self.trigger_subscribe_messages()

    async def close(self):
        try:
            async with self.lock:
                if self.sqs_client is None:
                    return
                await self.sqs_client.close()
                # log.info('Message Queue[SQS] client is closed')

        except Exception as e:
            log.error(e.__str__())


class EventBridgeResourceHandler(ResourceHandler):

    def __init__(self, session: aioboto3.Session):
        super().__init__()
        self.max_timeout = MQ_CONNECT_TIMEOUT

        self.lock = asyncio.Lock()
        self.session = session
        self.events_client = None

    async def initial(self):
        try:
            async with self.lock:
                if self.events_client is None:
                    async with self.session.client('events', config=mq_config) as events_client:
                        self.events_client = events_client
                        response = await self.events_client.describe_event_bus()
                        log.info('Event Bus[EventBridge] Connection is healthy, EventBusArn: %s',
                                 response['Arn'])

        except Exception as e:
            log.error(e.__str__())
            async with self.lock:
                async with self.session.client('events', config=mq_config) as events_client:
                    self.events_client = events_client

    async def accessing(self, **kwargs):
        async with self.lock:
            if self.events_client is None:
                await self.initial()

            return self.events_client

    # Regular activation to maintain connections and connection pools
    async def probe(self):
        try:
            response = await self.events_client.describe_event_bus()
            log.info('Event Bus[EventBridge] Connection is healthy, EventBusArn: %s',
                     response['Arn'])
        except Exception as e:
            log.error(
                f'Event Bus[EventBridge] Connection Error: %s', e.__str__())
            await self.initial()

    async def close(self):
        try:
            async with self.lock:
                if self.events_client is None:
                    return
                await self.events_client.close()
                # log.info('Event Bus[EventBridge] client is closed')

        except Exception as e:
            log.error(e.__str__())
