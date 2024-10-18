import asyncio
import aioboto3
from botocore.config import Config
from ._resource import ResourceHandler
from ....configs.conf import (
    TABLE_ACCOUNT,
    DDB_CONNECT_TIMEOUT,
    DDB_READ_TIMEOUT,
    DDB_MAX_ATTEMPTS,
)
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


ddb_config = Config(
    connect_timeout=DDB_CONNECT_TIMEOUT,
    read_timeout=DDB_READ_TIMEOUT,
    retries={'max_attempts': DDB_MAX_ATTEMPTS}
)


class DynamoDBResourceHandler(ResourceHandler):

    def __init__(self, session: aioboto3.Session):
        super().__init__()
        self.max_timeout = DDB_CONNECT_TIMEOUT

        self.session = session
        self.lock = asyncio.Lock()
        self.db_rsc = None


    async def initial(self):
        try:
            async with self.lock:
                if self.db_rsc is None:
                    async with self.session.resource('dynamodb', config=ddb_config) as db_resource:
                        self.db_rsc = db_resource
                        meta = await self.db_rsc.meta.client.describe_table(TableName=TABLE_ACCOUNT)
                        log.info('Initial DynamoDB describe_table ResponseMetadata: %s', meta['ResponseMetadata'])

        except Exception as e:
            log.error(e.__str__())
            async with self.lock:
                async with self.session.resource('dynamodb', config=ddb_config) as db_resource:
                    self.db_rsc = db_resource


    async def accessing(self, **kwargs):
        async with self.lock:
            if self.db_rsc is None:
                await self.initial()

            return self.db_rsc


    # Regular activation to maintain connections and connection pools
    async def probe(self):
        try:
            # meta = await self.db_rsc.Table(TABLE_CACHE).load()  # 替換 'YourTableName' 為你的表名
            meta = await self.db_rsc.meta.client.describe_table(TableName=TABLE_ACCOUNT)
            log.info('DynamoDB describe_table HTTPStatusCode: %s', meta['ResponseMetadata']['HTTPStatusCode'])
        except Exception as e:
            log.error(f'DynamoDB Client Error: %s', e.__str__())
            await self.initial()


    async def close(self):
        try:
            async with self.lock:
                if self.db_rsc is None:
                    return
                await self.db_rsc.meta.client.close()
                # log.info('DynamoDB client is closed')

        except Exception as e:
            log.error(e.__str__())
