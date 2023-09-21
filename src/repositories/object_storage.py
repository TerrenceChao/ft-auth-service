from abc import ABC, abstractmethod


class IObjectStorage(ABC):

    @abstractmethod
    def init(self, bucket, version):
        pass

    @abstractmethod
    def update(self, bucket, version, newdata):
        pass

    @abstractmethod
    def delete(self, bucket):
        pass

    @abstractmethod
    def find(self, bucket):
        pass
