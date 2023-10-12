from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, List, Any, Optional
from pydantic import EmailStr, BaseModel
from ..infra.db.nosql.schemas import *

class UpdatePasswordParams(BaseModel):
    pass_hash: str
    pass_salt: str
    email: EmailStr


class IAuthRepository(ABC):

    @abstractmethod
    def get_account_by_email(self, auth_db: Any, account_db: Any, email: EmailStr, fields: List):
        pass

    @abstractmethod
    def create_account(self, auth_db: Any, account_db: Any, auth: FTAuth, account: Account):
        pass

    @abstractmethod
    def delete_account_by_email(self, auth_db: Any, account_db: Any, email: EmailStr):
        pass

    @abstractmethod
    def find_account(self, db: Any, aid: Decimal):
        pass

    @abstractmethod
    def find_auth(self, db: Any, email: EmailStr):
        pass

    @abstractmethod
    def update_password(self, db: Any, update_password_params: UpdatePasswordParams):
        pass
