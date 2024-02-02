from src.repositories.auth_repository import IAuthRepository
from src.repositories.object_storage import IObjectStorage
from src.services.sso_auth_service import SSOAuthService
from src.infra.apis.facebook import FBLoginRepository
from src.models.sso_api import RedirectUrl
from src.configs.constants import AccountType
from fastapi.responses import RedirectResponse
from ..models.auth_value_objects import AccountVO
from ..infra.apis.email import Email
from ..configs.exceptions import *
import logging as log

from typing import Any

class FBAuthService(SSOAuthService):
    def __init__(self, auth_repo: IAuthRepository, obj_storage: IObjectStorage, email: Email, fb: FBLoginRepository):
        super().__init__(auth_repo, obj_storage, email)
        self.fb = fb
    
    def register_or_login(self, code: str, state: str, auth_db: Any, account_db: Any) -> AccountVO:
        oauth_data = self.fb.oauth(code)
        if not oauth_data or not oauth_data.access_token:
            return f'there is no accesstoken \n {oauth_data}'
        user_info = self.fb.get_user_info(access_token=oauth_data.access_token)
        general_user_info = self.fb.fb_user_info_to_general(user_info)
        return self._register_or_login(general_user_info, state, AccountType.FB, auth_db, account_db)
    
    def dialog(self, role: str, region: str) -> RedirectUrl:
        state_payload = self._make_state_payload_json(role, region)
        return self.fb.dialog(state_payload)
