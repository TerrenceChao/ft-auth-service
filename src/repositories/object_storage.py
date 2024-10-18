from abc import ABC, abstractmethod


class IObjectStorage(ABC):

    @abstractmethod
    async def init(self, bucket, version):
        pass

    @abstractmethod
    async def update(self, bucket, version, newdata):
        pass

    @abstractmethod
    async def delete(self, bucket):
        pass

    @abstractmethod
    async def find(self, bucket):
        pass
