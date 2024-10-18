import asyncio
import aioboto3
from typing import Dict
from .handlers._resource import ResourceHandler
from .handlers.storage_resource import S3ResourceHandler
from .handlers.db_resource import DynamoDBResourceHandler
from .handlers.email_resource import SESClientHandler
from .handlers.http_resource import HttpResourceHandler
from ...configs.conf import PROBE_CYCLE_SECS
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)



class GlobalResourceManager:
    def __init__(self):
        session = aioboto3.Session()
        self.resources: Dict[str, ResourceHandler] = {
            'storage': S3ResourceHandler(session),
            'dynamodb': DynamoDBResourceHandler(session),
            'email': SESClientHandler(session),
            'http': HttpResourceHandler(),
        }

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




resource_manager = GlobalResourceManager()
