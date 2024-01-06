from typing import Any, Optional
from pydantic import EmailStr
from dataclasses import dataclass, asdict
import json

from src.services.auth_service import AuthService
from src.models.sso_api import StatePayload, GeneralUserInfo
from src.infra.apis.facebook import GetUserInfoResponse
from src.configs.constants import AccountType
from ..repositories.auth_repository import IAuthRepository
from ..repositories.object_storage import IObjectStorage
from ..models.auth_value_objects import AccountVO
from ..infra.utils import auth_util
from ..infra.apis.email import Email
from ..configs.exceptions import *
import logging as log


@dataclass
class PreAccountData:
    role: str
    region: str
    email: str
    sso_id: str

log.basicConfig(filemode='w', level=log.INFO)


class SSOAuthService(AuthService):
    def __init__(self, auth_repo: IAuthRepository, obj_storage: IObjectStorage, email: Email):
        super().__init__(auth_repo, obj_storage, email)
        self.__cls_name = self.__class__.__name__

   
    def _register_or_login(
        self,
        user_info: GeneralUserInfo,
        state: str,
        account_type: AccountType,
        auth_db: Any,
        account_db: Any,
    ) -> AccountVO:
        state_payload = self._parse_state(state)
        version = self.__check_if_email_is_registered(email=user_info.email)
 
        if not version:
            return self.__login(state_payload, user_info, auth_db, account_db)
        else:
            return self.__register(
                state_payload,
                user_info,
                account_type,
                version,
                auth_db,
                account_db,
            )

    """
    檢查 email 有沒註冊過
        去 S3 檢查 email 有沒註冊過，若沒有 則先寫入 email + version
    """
    def __check_if_email_is_registered(self, email: EmailStr) -> Optional[str]:
        # Is the email registered with S3?
        email_info = self.obj_storage.find(bucket=email)
        if email_info is not None:
            return ""

        # save email and version into S3 if it's not registered
        version = auth_util.gen_random_string(10)
        version = self.obj_storage.init(bucket=email, version=version)
        return version  # all good!

    def __login(      
        self,  
        state_payload: StatePayload,
        user_info: GetUserInfoResponse,
        auth_db: Any,
        account_db: Any,
    ) -> AccountVO:
        auth = self.__validation(user_info.email, user_info.id, state_payload.region, auth_db)

        aid = auth['aid']
        account_vo = self.find_account(aid, account_db)
        return account_vo

    def __register(
        self,
        state_payload: StatePayload,
        user_info: GetUserInfoResponse,
        account_type: AccountType,
        version: str,
        auth_db: Any,
        account_db: Any,
    ) -> AccountVO:
        auth, account = self.__generate_account_data(
            state_payload, user_info, account_type, version
        )
        return self.save_account_data(auth, account, auth_db, account_db)

    """
    產生帳戶資料
        1. 更新 email 資料到 S3
            檢查 version, 將 email + register_region 覆寫至 S3
        2. 產生 DynamoDB 需要的帳戶資料
    """
    def __generate_account_data(
        self,
        state_payload: StatePayload,
        user_info: GeneralUserInfo,
        account_type: AccountType,
        version: str,
    ):
        # 1. 更新 email 資料到 S3
        pre_account_data = PreAccountData(
            role=state_payload.role,
            region=state_payload.region,
            email=user_info.email,
            sso_id=user_info.id,
        )
        self.obj_storage.update(
            bucket=pre_account_data.email,
            version=version,
            newdata={"region": pre_account_data.region},
        )

        # 為了配合舊 code 這邊把它轉成 dict 處理
        # TODO: 找時間要把舊 code 改成用 PreAccountData 傳進來
        pre_account_data_d = asdict(pre_account_data)
        auth, account = auth_util.gen_account_data(pre_account_data_d, account_type)
        return (auth, account)  # all good!
 

    def _parse_state(self, state: str) -> StatePayload:
        return StatePayload.parse_obj(json.loads(state))

    def _make_state_payload_json(self, role: str, region: str) -> str:
        state_payload = StatePayload(
            role=role,
            region=region,
        )
        return json.dumps(state_payload.dict())

    '''
    驗證登入資訊
        1. 從 DynamoDB (auth) 取得 auth
        2. not found 錯誤處理
        3. validation sso_id
        4. return auth
    '''
    def __validation(
        self,
        email: EmailStr,
        sso_id: str,
        current_region: str,
        auth_db: Any,
    ) -> Any:
        # 1. 從 DynamoDB (auth) 取得 auth
        auth = self.auth_repo.find_auth(db=auth_db, email=email)
        
        # 2. not found 錯誤處理
        if auth is None:
            email_info = self.obj_storage.find(bucket=email)
            if email_info is None:
                raise NotFoundException(msg='user_not_found')

            # email_info, S3 有，但是這地區的 DB 沒有，有可能在其他地區的 DB
            elif 'region' in email_info and email_info['region'] != current_region:
                raise ForbiddenException(data=email_info, msg='wrong_region')

            else:
                # email_info 有問題, 表示 S3:
                # 1. 有 version/region, 且 region 也顯示在該地區 -> S3有, DB沒有。
                # 2. 有 version, 沒 region
                # 這結果 超級有問題!!!
                log.error(f'{self.__cls_name}.login [register_fail]!!! \
                    email:%s, auth:%s, email_info:%s',
                    email, auth, email_info)
                raise ServerException(msg='register_fail')
            
        # 3. validation sso_id 
        stored_sso_id = auth.get('sso_id', None)
        if stored_sso_id != sso_id:
            raise UnauthorizedException(msg='error_authorization') 

        # 4. return auth
        return auth  # all good!
