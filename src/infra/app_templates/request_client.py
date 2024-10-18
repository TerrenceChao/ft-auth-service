from abc import ABC, abstractmethod
from typing import Dict
from .models.client_response import ClientResponse


class IRequestClient(ABC):
    @abstractmethod
    async def simple_get(self, url: str, params: Dict = None, headers: Dict = None) -> (Dict[str, str] | None):
        pass
    
    @abstractmethod
    async def get(self, url: str, params: Dict = None, headers: Dict = None) -> ClientResponse:
        pass
    
    @abstractmethod
    async def simple_post(self, url: str, json: Dict, headers: Dict = None) -> (Dict[str, str] | None):
        pass

    @abstractmethod
    async def post(self, url: str, json: Dict, headers: Dict = None) -> ClientResponse:
        pass

    @abstractmethod
    async def simple_put(self, url: str, json: Dict = None, headers: Dict = None) -> (Dict[str, str] | None):
        pass
    
    @abstractmethod
    async def put(self, url: str, json: Dict = None, headers: Dict = None) -> ClientResponse:
        pass
    
    @abstractmethod
    async def simple_delete(self, url: str, params: Dict = None, headers: Dict = None) -> (Dict[str, str] | None):
        pass

    @abstractmethod
    async def delete(self, url: str, params: Dict = None, headers: Dict = None) -> ClientResponse:
        pass
