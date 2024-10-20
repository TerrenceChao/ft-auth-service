from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, List, Any, Optional, Tuple
from pydantic import EmailStr, BaseModel
from ..infra.db.nosql.auth_schemas import *

class UpdatePasswordParams(BaseModel):
    pass_hash: str
    pass_salt: str
    email: EmailStr


class IAuthRepository(ABC):

    @abstractmethod
    async def get_account_by_email(self, auth_db: Any, account_db: Any, email: EmailStr, fields: List):
        pass

    @abstractmethod
    async def create_account(self, auth_db: Any, account_db: Any, auth: FTAuth, account: Account) -> Tuple[FTAuth, Account]:
        pass

    @abstractmethod
    async def delete_account(self, auth_db: Any, account_db: Any, auth: FTAuth):
        pass

    @abstractmethod
    async def find_account(self, db: Any, aid: Decimal):
        pass
    
    @abstractmethod
    async def find_account_by_role_id(self, db: Any, role_id: Decimal):
        pass

    @abstractmethod
    async def find_auth(self, db: Any, email: EmailStr):
        pass

    @abstractmethod
    async def update_password(self, db: Any, update_password_params: UpdatePasswordParams):
        pass
