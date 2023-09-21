from abc import abstractmethod
from decimal import Decimal
from typing import Dict, List, Any, Optional
from pydantic import EmailStr


class IAuthRepository:

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
    def authentication(self, db: Any, email: EmailStr, pw: str, match_password: Any):
        pass

    @abstractmethod
    def find_account(self, db: Any, aid: Decimal):
        pass

    @abstractmethod
    def reset_password(self, db: Any, aid: Decimal, pw: str):
        pass
