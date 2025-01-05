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

    async def initial(self):
       pass


    async def accessing(self, **kwargs):
        async with self.session.resource('dynamodb', config=ddb_config) as db_resource:
            return db_resource


    # Regular activation to maintain connections and connection pools
    async def probe(self):
        try:
            # meta = await self.db_rsc.Table(TABLE_CACHE).load()  # 替換 'YourTableName' 為你的表名
            async with self.session.resource('dynamodb', config=ddb_config) as db_resource:
                meta = await db_resource.meta.client.describe_table(TableName=TABLE_ACCOUNT)
                log.info('DynamoDB describe_table HTTPStatusCode: %s', meta['ResponseMetadata']['HTTPStatusCode'])
        except Exception as e:
            log.error(f'DynamoDB Client Error: %s', e.__str__())

    async def close(self):
        pass
