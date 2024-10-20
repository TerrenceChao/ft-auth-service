import asyncio
import aioboto3
from botocore.config import Config
from ._resource import ResourceHandler
from ....configs.conf import (
    FT_BUCKET,
    S3_CONNECT_TIMEOUT,
    S3_READ_TIMEOUT,
    S3_MAX_ATTEMPTS,
    S3_REGION,
)
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


s3_config = Config(
    connect_timeout=S3_CONNECT_TIMEOUT,
    read_timeout=S3_READ_TIMEOUT,
    retries={'max_attempts': S3_MAX_ATTEMPTS}
)


class S3ResourceHandler(ResourceHandler):

    def __init__(self, session: aioboto3.Session):
        super().__init__()
        self.max_timeout = S3_CONNECT_TIMEOUT

        self.session = session
        self.lock = asyncio.Lock()
        self.storage_rsc = None


    async def initial(self):
        try:
            async with self.lock:
                if self.storage_rsc is None:
                    async with self.session.resource('s3', config=s3_config, region_name=S3_REGION) as storage_resource:
                        self.storage_rsc = storage_resource
                        meta = await self.storage_rsc.meta.client.head_bucket(Bucket=FT_BUCKET)
                        log.info('Initial GlobalObjectStorage[S3] head_bucket ResponseMetadata: %s', meta['ResponseMetadata'])

        except Exception as e:
            log.error(e.__str__())
            async with self.lock:
                async with self.session.resource('s3', config=s3_config, region_name=S3_REGION) as storage_resource:
                    self.storage_rsc = storage_resource


    async def accessing(self, **kwargs):
        async with self.lock:
            if self.storage_rsc is None:
                await self.initial()

            return self.storage_rsc


    # Regular activation to maintain connections and connection pools
    async def probe(self):
        try:
            # meta = await self.storage_rsc.
            meta = await self.storage_rsc.meta.client.head_bucket(Bucket=FT_BUCKET)
            log.info('GlobalObjectStorage[S3] head_bucket HTTPStatusCode: %s', meta['ResponseMetadata']['HTTPStatusCode'])
        except Exception as e:
            log.error(f'GlobalObjectStorage[S3] Client Error: %s', e.__str__())
            await self.initial()


    async def close(self):
        try:
            async with self.lock:
                if self.storage_rsc is None:
                    return
                await self.storage_rsc.meta.client.close()
                # log.info('GlobalObjectStorage[S3] client is closed')

        except Exception as e:
            log.error(e.__str__())
