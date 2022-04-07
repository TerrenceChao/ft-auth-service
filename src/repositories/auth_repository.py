from abc import abstractmethod
from typing import Dict, List, Any, Optional


class IAuthRepository:

    @abstractmethod
    def get_account_by_email(self, auth_db: Any, account_db: Any, email: str, fields: List):
        pass

    @abstractmethod
    def create_account(self, auth_db: Any, account_db: Any, email: str, data: Any):
        pass

    @abstractmethod
    def delete_account_by_email(self, auth_db: Any, account_db: Any, email: str):
        pass

    @abstractmethod
    def authentication(self, db: Any, email: str, pw: str, match_password: Any):
        pass

    @abstractmethod
    def find_account(self, db: Any, aid: int):
        pass


