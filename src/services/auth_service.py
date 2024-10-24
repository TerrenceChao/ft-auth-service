from typing import Any, Union, Callable, Optional
from pydantic import EmailStr
from decimal import Decimal
import hashlib
import uuid

from src.configs.constants import AccountType
from ..repositories.auth_repository import IAuthRepository
from ..repositories.object_storage import IObjectStorage
from ..models.auth_value_objects import *
from ..infra.db.nosql.auth_schemas import FTAuth, Account
from ..infra.utils import auth_util
from ..infra.client.email import EmailClient
from ..configs.exceptions import *
from ..configs.conf import (TESTING, STAGE)
import logging as log

log.basicConfig(filemode='w', level=log.INFO)


class AuthService:
    def __init__(self, auth_repo: IAuthRepository, obj_storage: IObjectStorage, email: EmailClient):
        self.auth_repo = auth_repo
        self.obj_storage = obj_storage
        self.email = email
        self.__cls_name = self.__class__.__name__

    async def send_conform_code_by_email(
        self,
        email: EmailStr,
        confirm_code: str,
        sendby: str,
        auth_db: Any,
        account_db: Any
    ):
        res = None
        try:
            res = await self.auth_repo.get_account_by_email(
                auth_db=auth_db,
                account_db=account_db,
                email=email,
                fields=['email', 'region', 'role']
            )

        except ServerError as e:
            log.error(f'{self.__cls_name}.send_conform_code_by_email [lack with account_data] \
                email:%s, confirm_code:%s, sendby:%s, res:%s, err:%s',
                      email, confirm_code, sendby, res, e.__str__())
            raise ServerException(msg='incomplete_registered_user_information')

        try:
            sendby = str(sendby).lower()
            if res is None:
                if sendby == 'no_exist':
                    if STAGE != TESTING:    # don't send email in DEV stage
                        await self.email.send_conform_code(email=email, confirm_code=confirm_code)
                    return 'email_sent'
                raise NotFoundException(msg='email_not_found')

            else:
                if sendby == 'registered':
                    if STAGE != TESTING:    # don't send email in DEV stage
                        await self.email.send_conform_code(email=email, confirm_code=confirm_code)
                    return 'email_sent'
                raise DuplicateUserException(msg='email_registered')

        except Exception as e:
            log.error(f'{self.__cls_name}.send_code_by_email [email sending error] \
                email:%s, confirm_code:%s, sendby:%s, res:%s, err:%s',
                      email, confirm_code, sendby, res, e.__str__())
            raise_http_exception(e=e, msg=e.msg if e.msg else 'unknow_error')

    '''
    註冊流程
        1. 檢查 email 有沒註冊過
        2. 產生帳戶資料
        3. 將帳戶資料寫入 DB
    '''

    async def signup(
        self,
        email: EmailStr,
        data: Any,
        auth_db: Any,
        account_db: Any,
    ) -> (SignupVO):
        try:
            # 1. 檢查 email 有沒註冊過
            version = await self.__check_if_email_is_registered(email)

            # 2. 產生帳戶資料
            auth, account = await self.__generate_account_data(
                email, data, version)

            # TODO: [2]. Close/disable account
            # 透過 auth_service.funcntion(...) 判斷是否允許 login/signup; 並且調整註解

            # 3. 將帳戶資料寫入 DB
            signup_vo = await self.save_account_data(auth, account, auth_db, account_db)
            return signup_vo

        except ClientException as e:
            raise ClientException(msg=e.msg, data=e.data)

        except NotAcceptableException as e:
            raise NotAcceptableException(msg=e.msg, data=e.data)

        except DuplicateUserException as e:
            raise DuplicateUserException(msg=e.msg, data=e.data)

        except ServerException as e:
            raise ServerException(msg=e.msg, data=e.data)

        except Exception as e:
            log.error(f'{self.__cls_name}.signup [unknown_err] \
                email:%s, data:%s, err:%s',
                      email, data, e.__str__())
            raise ServerException(msg='unknown_err')

    '''
    登入流程
        1. 驗證登入資訊
        2. 取得帳戶資料
    '''

    async def login(
        self,
        email: EmailStr,
        data: Any,
        current_region: str,
        auth_db: Any,
        account_db: Any,
    ):
        try:
            # TODO: [2]. Close/disable account
            # 透過 auth_service.funcntion(...) 判斷是否允許 login/signup; 並且調整註解

            # 1. 驗證登入資訊
            pw = data['pass']
            auth = await self.__validation(email, pw, current_region, auth_db)

            # 2. 取得帳戶資料
            aid = auth['aid']
            account_vo = await self.find_account(aid, account_db)
            return account_vo

        except ClientException as e:
            raise ClientException(msg=e.msg, data=e.data)

        except UnauthorizedException as e:
            raise UnauthorizedException(msg=e.msg, data=e.data)

        except ForbiddenException as e:
            # important! 'region' in S3 needs to be returned
            raise ForbiddenException(msg=e.msg, data=e.data)

        except NotFoundException as e:
            raise NotFoundException(msg=e.msg, data=e.data)

        except NotAcceptableException as e:
            raise NotAcceptableException(msg=e.msg, data=e.data)

        except ServerException as e:
            raise ServerException(msg=e.msg, data=e.data)

        except Exception as e:
            log.error(f'{self.__cls_name}.signup [unknown_err] \
                email:%s, data:%s, err:%s',
                      email, data, e.__str__())
            raise ServerException(msg='unknown_err')

    async def update_password(
        self, db: Any, email: EmailStr, new_pw: str, origin_pw: Optional[str] = None
    ) -> (UpdatePasswordDTO):
        try:
            pass_salt = auth_util.gen_pass_salt()
            params = UpdatePasswordDTO(
                email=email,
                pass_salt=pass_salt,
                pass_hash=auth_util.gen_password_hash(new_pw, pass_salt),
            )

            if origin_pw:
                account_data = await self.auth_repo.find_auth(db=db, email=email)
                if account_data is None:
                    raise NotFoundException(msg='user_not_found')

                if not auth_util.match_password(
                    pass_hash=account_data['pass_hash'], pw=origin_pw, pass_salt=account_data['pass_salt']
                ):
                    raise ForbiddenException(msg='Invalid Password')

            auth: FTAuth = await self.auth_repo.update_password(db=db, update_password_params=params)
            return params.set_role_id(role_id=auth.role_id)

        except NotFoundException as e:
            raise NotFoundException(msg=e.msg)

        except ForbiddenException as e:
            raise ForbiddenException(msg=e.msg)

        except Exception as e:
            log.error(f'{self.__cls_name}.update_password [unknown_err] \
                params:%s, err:%s', params, e.__str__())

        # raise exception avoid send remote event
        raise_http_exception(e, msg='unknown_err')



    async def send_reset_password_confirm_email(self, auth_db: Any, account_db: Any, email: EmailStr) -> (str):
        user = await self.auth_repo.get_account_by_email(auth_db=auth_db, account_db=account_db, email=email, fields=['aid'])
        if not user:
            raise ServerException(msg='invalid user')
        token = str(uuid.uuid1())
        await self.email.send_reset_password_comfirm_email(email=email, token=token)
        return token

    async def update_password_by_remote_event(self, db: Any, params: UpdatePasswordDTO):
        try:
            await self.auth_repo.update_password(db=db, update_password_params=params)
        except Exception as e:
            log.error(f'{self.__cls_name}.update_password_by_remote_event [unknown_err] \
                params:%s, err:%s', params, e.__str__())
            raise_http_exception(e, msg='unknown_err')

    '''
    檢查 email 有沒註冊過
        去 S3 檢查 email 有沒註冊過，若沒有 則先寫入 email + version
    '''

    async def __check_if_email_is_registered(self, email: EmailStr):
        # Is the email registered with S3?
        email_info = await self.obj_storage.find(bucket=email)
        if email_info is not None:
            raise DuplicateUserException(data=email_info, msg='registered')

        # save email and version into S3 if it's not registered
        version = auth_util.gen_random_string(10)
        version = await self.obj_storage.init(bucket=email, version=version)
        return version  # all good!

    '''
    產生帳戶資料
        1. 更新 email 資料到 S3
            檢查 version, 將 email + register_region 覆寫至 S3
        2. 產生 DynamoDB 需要的帳戶資料
    '''

    async def __generate_account_data(self, email: EmailStr, data: Any, version: str):
        # 1. 更新 email 資料到 S3
        region = data['region']
        await self.obj_storage.update(
            bucket=email, version=version, newdata={'region': region})

        # 2. 產生 DynamoDB 需要的帳戶資料
        data['email'] = email
        auth, account = auth_util.gen_account_data(data, AccountType.FT)
        return (auth, account)  # all good!

    '''
    將帳戶資料寫入 DB
        1. 將帳戶資料寫入 DynamoDB
            res = { aid, region, email, email2, is_active, role, role_id } = account
        2. 錯誤處理..
            a. 先嘗試刪除 DynamoDB
            b. 再嘗試刪除 S3
    '''

    async def save_account_data(
        self,
        auth: FTAuth,
        account: Account,
        auth_db: Any,
        account_db: Any,
    ) -> (SignupVO):
        res = None
        try:
            # 1. 將帳戶資料寫入 DynamoDB
            (auth, account) = await self.auth_repo.create_account(
                auth_db=auth_db, account_db=account_db, auth=auth, account=account)
            return SignupVO(auth=auth, account=account)

        except Exception as e:
            log.error(f'{self.__cls_name}.signup [db_create_err] \
                auth:%s, account:%s, res:%s, err:%s',
                      auth, account, res, e.__str__())

            # 2. 錯誤處理..
            try:
                # create_account is transactional, so we don't need to delete account
                # await self.auth_repo.delete_account(
                #     auth_db=auth_db, account_db=account_db, auth=auth)
                await self.obj_storage.delete(bucket=auth.email)

            except Exception as e:
                log.error(f'{self.__cls_name}.signup [rollback_err] \
                    auth:%s, account:%s, res:%s, err:%s',
                          auth, account, res, e.__str__())
                raise ServerException(msg='rollback_err')

            raise ServerException(msg='db_create_err')

    '''
    從註冊地同步用戶資料: 將帳戶資料寫入 DynamoDB
    '''

    async def duplicate_account_by_registered_region(
        self,
        auth: FTAuth,
        account: Account,
        auth_db: Any,
        account_db: Any,
    ):
        res = None
        try:
            # 1. 檢查 email 有沒註冊過
            user = await self.auth_repo.get_account_by_email(
                auth_db=auth_db,
                account_db=account_db,
                email=auth.email,
                fields=['aid'])

            # 2. 若為新用戶，將資料寫入 DynamoDB
            if not user:
                (auth, account) = await self.auth_repo.create_account(
                    auth_db=auth_db, account_db=account_db, auth=auth, account=account)

            res = SignupVO(auth=auth, account=account)  # all good!

        except Exception as e:
            log.error(f'{self.__cls_name}.signup [db_create_err] \
                auth:%s, account:%s, err:%s',
                      auth, account, e.__str__())

            # 3. 錯誤處理..
            try:
                await self.auth_repo.delete_account(
                    auth_db=auth_db, account_db=account_db, auth=auth)

            except Exception as e:
                log.error(f'{self.__cls_name}.signup [rollback_err] \
                    auth:%s, account:%s, err:%s',
                          auth, account, e.__str__())
                raise ServerException(msg='rollback_err')

            raise ServerException(msg='db_create_err')

        return res

    '''
    驗證登入資訊
        1. 從 DynamoDB (auth) 取得 auth
        2. not found 錯誤處理
        3. validation password
        4. return auth
    '''

    async def __validation(
        self,
        email: EmailStr,
        pw: str,
        current_region: str,
        auth_db: Any,
    ):
        # 1. 從 DynamoDB (auth) 取得 auth
        auth = await self.auth_repo.find_auth(db=auth_db, email=email)

        # 2. not found 錯誤處理
        if auth is None:
            email_info = await self.obj_storage.find(bucket=email)
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

        # 3. validation password
        pass_hash = auth['pass_hash']
        pass_salt = auth['pass_salt']
        if not auth_util.match_password(pass_hash=pass_hash, pw=pw, pass_salt=pass_salt):
            raise UnauthorizedException(msg='error_password')

        # 4. return auth
        return auth  # all good!

    '''
    取得帳戶資料
        從 DynamoDB (accounts) 取得必要的帳戶資料
    '''

    async def find_account(self, aid: str, account_db: Any):
        res = await self.auth_repo.find_account(db=account_db, aid=aid)
        if res is None:
            raise NotFoundException(msg='account_not_found')

        return AccountVO.parse_obj(res)

    # TODO: [2]. Close/disable account
    # 新增一個 funcntion 判斷是否允許 login/signup：
    # 1. 是否在三個月內有被停用，
    #       若無，則繼續執行其他程序
    #       若有，且在三個月內，則 API直接回傳 'account_closed'
    #       若有，且超過三個月，則 '請開發者決定' 是否允許重新開啟帳號? 並允許login/signup????? 後面的機制如何?
    # 2. 注意 error handling

    # TODO: 新增 functions 做 API:
    # [1]. Update password
    # [2]. Close/disable account
    # [3]. Forgot password
