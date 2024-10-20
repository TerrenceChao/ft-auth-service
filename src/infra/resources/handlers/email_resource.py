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
                        send_quota = await self.email_client.get_send_quota()
                        log.info('Email[SES] get_send_quota ResponseMetadata: %s', send_quota['ResponseMetadata'])

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
            send_quota = await self.email_client.get_send_quota()
            log.info('Email[SES] get_send_quota HTTPStatusCode: %s', send_quota['ResponseMetadata']['HTTPStatusCode'])
        except Exception as e:
            log.error(f'Email[SES] Client Error: %s', e.__str__())
            await self.initial()


    async def close(self):
        try:
            async with self.lock:
                if self.email_client is None:
                    return
                await self.email_client.close()
                # log.info('Email[SES] client is closed')

        except Exception as e:
            log.error(e.__str__())
