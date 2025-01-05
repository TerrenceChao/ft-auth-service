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
    retries={"max_attempts": S3_MAX_ATTEMPTS},
)


class S3ResourceHandler(ResourceHandler):

    def __init__(self, session: aioboto3.Session):
        super().__init__()
        self.max_timeout = S3_CONNECT_TIMEOUT

        self.session = session
        self.storage_rsc = None

    async def initial(self):
        pass

    async def accessing(self, **kwargs):
        async with self.session.resource(
            "s3", config=s3_config, region_name=S3_REGION
        ) as storage_resource:
            return storage_resource

    # Regular activation to maintain connections and connection pools
    async def probe(self):
        try:
            async with self.session.resource(
                "s3", config=s3_config, region_name=S3_REGION
            ) as storage_resource:
                meta = await storage_resource.meta.client.head_bucket(Bucket=FT_BUCKET)
                log.info(
                    "GlobalObjectStorage[S3] head_bucket HTTPStatusCode: %s",
                    meta["ResponseMetadata"]["HTTPStatusCode"],
                )
        except Exception as e:
            log.error(f"GlobalObjectStorage[S3] Client Error: %s", e.__str__())
            # await self.initial()

    async def close(self):
        pass
