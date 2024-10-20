from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any
from ..models.event_vos import *

class IEventRepository(ABC):

    @abstractmethod
    async def append_pub_event_log(self, event: PubEventDetailVO):
        pass

    @abstractmethod
    async def append_sub_event_log(self, event: SubEventDetailVO):
        pass
