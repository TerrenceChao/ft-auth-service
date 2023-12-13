from typing import Any, Union, Callable, Optional, Tuple
from pydantic import EmailStr, BaseModel
from decimal import Decimal
from dataclasses import dataclass, asdict
from fastapi.responses import RedirectResponse
import hashlib
import json
import uuid

from src.models.sso_api import StatePayload, GeneralUserInfo
from src.infra.apis.facebook import GetUserInfoResponse
from src.configs.constants import AccountType
from src.infra.apis.facebook import FBLoginRepository
from src.infra.apis.google import GoogleLoginRepository
from ..repositories.auth_repository import IAuthRepository, UpdatePasswordParams
from ..repositories.object_storage import IObjectStorage
from ..models.auth_value_objects import AccountVO
from ..infra.db.nosql.schemas import FTAuth, Account
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

class SSORepositories:

    def __init__(self, fb: FBLoginRepository, google: GoogleLoginRepository) -> None:
        self.fb = fb
        self.google = google


class SSOService:
    def __init__(
        self, auth_repo: IAuthRepository, obj_storage: IObjectStorage, email: Email,  sso_repositories: SSORepositories,
    ) -> None:
        self.auth_repo = auth_repo
        self.obj_storage = obj_storage
        self.email = email
        self.sso_repositories = sso_repositories
        self.__cls_name = self.__class__.__name__

    def fb_register_or_login(self, code: str, state: str, auth_db: Any, account_db: Any) -> AccountVO:
        oauth_data = self.sso_repositories.fb.oauth(code)
        if not oauth_data or not oauth_data.access_token:
            return f'there is no accesstoken \n {oauth_data}'
        user_info = self.sso_repositories.fb.get_user_info(access_token=oauth_data.access_token)
        general_user_info = self.sso_repositories.fb.fb_user_info_to_general(user_info)
        return self._register_or_login(general_user_info, state, AccountType.FB, auth_db, account_db)
    
    def fb_dialog(self, role: str, region: str) -> RedirectResponse:
        state_payload = self._make_state_payload_json(role, region)
        return self.sso_repositories.fb.dialog(state_payload)
    
    def google_dialog(self, role: str, region: str) -> RedirectResponse:
        state_payload = self._make_state_payload_json(role, region)
        return self.sso_repositories.google.auth(state_payload)

    def google_register_or_login(self, code: str, state: str, auth_db: Any, account_db: Any):
        oauth_data = self.sso_repositories.google.token(code)
        if not oauth_data or not oauth_data.id_token:
            return f'there is no accesstoken \n {oauth_data}'
        user_info = self.sso_repositories.google.user_info(oauth_data.id_token)
        general_user_info = self.sso_repositories.google.google_user_info_to_general(user_info)
        return self._register_or_login(general_user_info, state, AccountType.GOOGLE, auth_db, account_db)


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
        account_vo = self.__find_account(aid, account_db)
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
        return self.__save_account_data(auth, account, auth_db, account_db)

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

    """
        將帳戶資料寫入 DB
        1. 將帳戶資料寫入 DynamoDB
            res = { aid, region, email, email2, is_active, role, role_id } = account
        2. 錯誤處理..
            a. 先嘗試刪除 DynamoDB
            b. 再嘗試刪除 S3
    """
    def __save_account_data(
        self,
        auth: FTAuth,
        account: Account,
        auth_db: Any,
        account_db: Any,
    ) -> AccountVO:
        res = None
        try:
            # 1. 將帳戶資料寫入 DynamoDB
            res = self.auth_repo.create_account(
                auth_db=auth_db, account_db=account_db, auth=auth, account=account
            )
            return AccountVO.parse_obj(res)  # all good!

        except Exception as e:
            log.error(
                f"{self.__cls_name}.signup [db_create_err] \
                auth:%s, account:%s, res:%s, err:%s",
                auth,
                account,
                res,
                e.__str__(),
            )

            # 2. 錯誤處理..
            try:
                email = auth.email
                self.auth_repo.delete_account_by_email(
                    auth_db=auth_db, account_db=account_db, email=email
                )
                self.obj_storage.delete(bucket=email)

            except Exception as e:
                log.error(
                    f"{self.__cls_name}.signup [rollback_err] \
                    auth:%s, account:%s, res:%s, err:%s",
                    auth,
                    account,
                    res,
                    e.__str__(),
                )
                raise ServerException(msg="rollback_err")

            raise ServerException(msg="db_create_err")

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
    

    '''
    取得帳戶資料
        從 DynamoDB (accounts) 取得必要的帳戶資料
    '''
    def __find_account(self, aid: str, account_db: Any) -> AccountVO:
        res = self.auth_repo.find_account(db=account_db, aid=aid)
        if res is None:
            raise NotFoundException(msg='account_not_found')

        return AccountVO.parse_obj(res)
