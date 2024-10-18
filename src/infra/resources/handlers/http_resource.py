import asyncio
import httpx
import json
from typing import List, Dict
from urllib.parse import urlparse
from ._resource import ResourceHandler
from ....configs.conf import (
    HTTP_TIMEOUT,
    HTTP_MAX_CONNECTS,
    HTTP_MAX_KEEPALIVE_CONNECTS,
    HTTP_KEEPALIVE_EXPIRY,
)
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


timeout=httpx.Timeout(timeout=HTTP_TIMEOUT)
limits=httpx.Limits(
    max_connections=HTTP_MAX_CONNECTS,
    max_keepalive_connections=HTTP_MAX_KEEPALIVE_CONNECTS, 
    keepalive_expiry=HTTP_KEEPALIVE_EXPIRY,
)


class HttpResourceHandler(ResourceHandler):

    def __init__(self, domains: List[str] = [
        # TODO: 從 region_hosts 取得所有微服務的 domains
    ]):
        super().__init__()
        # update max_timeout
        self.max_timeout = HTTP_TIMEOUT

        self.resource_lock = asyncio.Lock()
        domains = [self.parse_domain(domain) for domain in domains]
        self.locks: Dict = {domain: asyncio.Lock() for domain in domains}  # 为每个域名创建锁
        self.domain_clients: Dict = {domain: None for domain in domains}


    async def initial(self):
        for domain in self.domain_clients.keys():
            self.domain_clients[domain] = httpx.AsyncClient(timeout=timeout, limits=limits)


    async def accessing(self, url: str):
        if url is None:
            raise Exception('url is a must')

        domain = self.parse_domain(url)
        if not domain in self.domain_clients:
            await self.__init_lock(domain)
            client = await self.__init_client(domain)
        else:
            client = self.domain_clients.get(domain, None)

        if not client or client.is_closed:
            client = await self.__init_client(domain)

        return client


    # Regular activation to maintain connections and connection pools
    async def probe(self):
        for domain, client in self.domain_clients.items():
            try:
                response = await client.head(f'http://{domain}/')  # 发送 HEAD 请求，使用 HEAD 请求检查域名是否可达
                if response.status_code >= 400:
                    raise Exception(json.dumps(response.json()))

            except Exception as e:  # 捕捉 HTTP 錯誤
                log.error('Http Connection Error: %s', e)
                await self.__init_client(domain)  # 重新建立連線


    async def close(self):
        for domain, client in self.domain_clients.items():
            if client is None:
                continue

            await client.aclose()
            self.domain_clients[domain] = None
            log.info('HttpX domain connection is closed: %s', domain)
            


    async def __init_lock(self, domain: str):
        async with self.resource_lock: # 為一開始沒有 lock 的 domain 上 IO鎖
            if not domain in self.locks:
                self.locks.update({domain: asyncio.Lock()}) # 新增 lock 給新的 domain

    async def __init_client(self, domain: str) -> httpx.AsyncClient:
        async with self.locks[domain]:  # 使用锁来防止竞争
            client = self.domain_clients.get(domain, None)
            if not client or client.is_closed:
                client = self.domain_clients[domain] = httpx.AsyncClient(timeout=timeout, limits=limits)

        return client


    # 從 url 解析 domain
    def parse_domain(self, url):
        return urlparse(url).netloc  # 返回解析出的 domain
    
    @classmethod
    def Response(cls):
        return httpx.Response 
