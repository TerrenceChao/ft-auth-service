import asyncio
import aioboto3
from typing import Dict
from .handlers import *
from ...configs.conf import (
    PROBE_CYCLE_SECS,
    SQS_P_QUEUE_URL,  # for retry failed pub events
    SQS_S_QUEUE_URL,  # for retry failed sub events
)
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class GlobalResourceManager:
    def __init__(self, resources: Dict[str, ResourceHandler]):
        self.resources: Dict[str, ResourceHandler] = resources

    def get(self, resource: str) -> ResourceHandler:
        if resource not in self.resources:
            raise ValueError(f'ResourceHandler "{resource}" not found.')

        return self.resources[resource]

    async def initial(self):
        for resource in self.resources.values():
            await resource.initial()

    async def probe(self):
        for resource in self.resources.values():
            try:
                if not resource.timeout():
                    log.info(f' ==> probing {resource.__class__.__name__}')
                    await resource.probe()
                else:
                    await resource.close()

            except Exception as e:
                log.error('probe error: %s', e)

    # Regular activation to maintain connections and connection pools

    async def keeping_probe(self):
        while True:
            await asyncio.sleep(PROBE_CYCLE_SECS)
            await self.probe()

    async def close(self):
        for resource in self.resources.values():
            await resource.close()


session = aioboto3.Session()
resource_manager = GlobalResourceManager({
    'storage': S3ResourceHandler(session),
    'dynamodb': DynamoDBResourceHandler(session),
    'email': SESResourceHandler(session),
    'event_bus': EventBridgeResourceHandler(session),
    'failed_pub_mq_rsc': SQSResourceHandler(session=session, label='failed pub events DLQ', queue_url=SQS_P_QUEUE_URL),
    'failed_sub_mq_rsc': SQSResourceHandler(session=session, label='failed sub events DLQ', queue_url=SQS_S_QUEUE_URL),
    'http': HttpResourceHandler(),
})
