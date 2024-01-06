from src.repositories.auth_repository import IAuthRepository
from src.repositories.object_storage import IObjectStorage
from src.services.sso_auth_service import SSOAuthService
from src.infra.apis.google import GoogleLoginRepository

from src.configs.constants import AccountType
from fastapi.responses import RedirectResponse
from ..models.auth_value_objects import AccountVO
from ..infra.db.nosql.schemas import FTAuth, Account
from ..infra.utils import auth_util
from ..infra.apis.email import Email
from ..configs.exceptions import *
import logging as log

from typing import Any

class GoogleAuthService(SSOAuthService):
    def __init__(self, auth_repo: IAuthRepository, obj_storage: IObjectStorage, email: Email, google: GoogleLoginRepository):
        super().__init__(auth_repo, obj_storage, email)
        self.google = google
    
    def dialog(self, role: str, region: str) -> RedirectResponse:
        state_payload = self._make_state_payload_json(role, region)
        return self.google.auth(state_payload)

    def register_or_login(self, code: str, state: str, auth_db: Any, account_db: Any):
        oauth_data = self.google.token(code)
        if not oauth_data or not oauth_data.id_token:
            return f'there is no accesstoken \n {oauth_data}'
        user_info = self.google.user_info(oauth_data.id_token)
        general_user_info = self.google.google_user_info_to_general(user_info)
        return self._register_or_login(general_user_info, state, AccountType.GOOGLE, auth_db, account_db)

