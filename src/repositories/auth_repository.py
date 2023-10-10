from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, List, Any, Optional
from pydantic import EmailStr


class IAuthRepository(ABC):

    @abstractmethod
    def get_account_by_email(self, auth_db: Any, account_db: Any, email: EmailStr, fields: List):
        pass

    @abstractmethod
    def create_account(self, auth_db: Any, account_db: Any, email: EmailStr, data: Any):
        pass

    @abstractmethod
    def delete_account_by_email(self, auth_db: Any, account_db: Any, email: EmailStr):
        pass

    @abstractmethod
    def get_auth_by_email(self, db: Any, email: EmailStr):
        pass

    @abstractmethod
    def find_account(self, db: Any, aid: Decimal):
        pass


