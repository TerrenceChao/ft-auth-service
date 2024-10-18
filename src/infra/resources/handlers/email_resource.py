import asyncio
import aioboto3
from botocore.config import Config
from ._resource import ResourceHandler
from ....configs.conf import (
    SES_CONNECT_TIMEOUT,
    SES_READ_TIMEOUT,
    SES_MAX_ATTEMPTS,
)
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


ses_config = Config(
    connect_timeout=SES_CONNECT_TIMEOUT,
    read_timeout=SES_READ_TIMEOUT,
    retries={'max_attempts': SES_MAX_ATTEMPTS}
)


class SESResourceHandler(ResourceHandler):

    def __init__(self, session: aioboto3.Session):
        super().__init__()
        self.max_timeout = SES_CONNECT_TIMEOUT

        self.session = session
        self.lock = asyncio.Lock()
        self.email_client = None


    async def initial(self):
        try:
            async with self.lock:
                if self.email_client is None:
                    async with self.session.client('ses', config=ses_config) as email_client:
                        self.email_client = email_client
                        identities = await self.email_client.list_identities()
                        log.info('SES(Email) list_identities ResponseMetadata: %s', identities['ResponseMetadata'])

        except Exception as e:
            log.error(e.__str__())
            async with self.lock:
                async with self.session.client('ses', config=ses_config) as email_client:
                    self.email_client = email_client


    async def accessing(self, **kwargs):
        async with self.lock:
            if self.email_client is None:
                await self.initial()

            return self.email_client


    # Regular activation to maintain connections and connection pools
    async def probe(self):
        try:
            identities = await self.email_client.list_identities()
            log.info('SES(Email) list_identities HTTPStatusCode: %s', identities['ResponseMetadata']['HTTPStatusCode'])
        except Exception as e:
            log.error(f'SES(Email) Client Error: %s', e.__str__())
            await self.initial()


    async def close(self):
        try:
            async with self.lock:
                if self.email_client is None:
                    return
                await self.email_client.close()
                # log.info('SES(Email) client is closed')

        except Exception as e:
            log.error(e.__str__())
