from typing import Any, Union, Callable
from pydantic import EmailStr
from ..repositories.auth_repository import IAuthRepository
from ..repositories.object_storage import IObjectStorage
from ..infra.utils import auth_util
import logging as log

log.basicConfig(filemode='w', level=log.INFO)


class AuthService:
    def __init__(self, auth_repo: IAuthRepository, obj_storage: IObjectStorage, send_conform_code: Callable[[str, str], None]) -> None:
        self.auth_repo = auth_repo
        self.obj_storage = obj_storage
        self.send_conform_code = send_conform_code
        pass

    async def send_conform_code_by_email(
        self,
        email: EmailStr,
        confirm_code: str,
        sendby: str,
        auth_db: Any,
        account_db: Any
    ) -> (Union[str, None], Union[str, None]):
        res, err = self.auth_repo.get_account_by_email(
            auth_db=auth_db,
            account_db=account_db,
            email=email,
            fields=["email", "region", "role"]
        )
        if err:
            return (None, err)

        sendby = str(sendby).lower()
        if res == None:
            if sendby == "no_exist":
                await self.send_conform_code(email=email, confirm_code=confirm_code)
                return ("email_sent", None)
            return (None, "email_not_found")

        else:
            if sendby == "registered":
                await self.send_conform_code(email=email, confirm_code=confirm_code)
                return ("email_sent", None)
            return (None, "email_registered")

    """
    註冊流程
        1. 檢查 email 有沒註冊過
        2. 產生帳戶資料
        3. 將帳戶資料寫入 DB
    """
    def signup(
        self,
        email: EmailStr,
        data: Any,
        auth_db: Any,
        account_db: Any,
    ) -> (Union[Any, None], Union[str, None]):
        # 1. 檢查 email 有沒註冊過
        email_info_or_version, err = self.__check_if_email_is_registered(email)
        if err:
            return (email_info_or_version, err)

        # 2. 產生帳戶資料
        account_data, err = self.__generate_account_data(
            email, data, email_info_or_version)
        if err:
            return (None, err)

        # TODO: [2]. Close/disable account
        # 透過 auth_service.funcntion(...) 判斷是否允許 login/signup; 並且調整註解

        # 3. 將帳戶資料寫入 DB
        return self.__save_account_data(email, account_data, auth_db, account_db)

    """
    登入流程
        1. 驗證登入資訊
        2. 取得帳戶資料
    """
    def login(
        self,
        email: EmailStr,
        data: Any,
        current_region: str,
        auth_db: Any,
        account_db: Any,
    ) -> (Union[Any, None], Union[str, None]):

        # TODO: [2]. Close/disable account
        # 透過 auth_service.funcntion(...) 判斷是否允許 login/signup; 並且調整註解

        # 1. 驗證登入資訊
        aid, err = self.__validation(email, data, current_region, auth_db)
        if err:
            return (None, err)

        # 2. 取得帳戶資料
        return self.__find_account(aid, account_db)

    """
    檢查 email 有沒註冊過
        去 S3 檢查 email 有沒註冊過，若沒有 則先寫入 email + version
    """
    def __check_if_email_is_registered(self, email: EmailStr) -> (Union[Any, None], Union[str, None]):
        # Is the email registered with S3?
        email_info, err = self.obj_storage.find(bucket=email)
        if err:
            return (None, "storage_read_err")

        if email_info:
            return (email_info, "registered")

        # save email and version into S3 if it's not registered
        version = auth_util.gen_random_string(10)
        version, err = self.obj_storage.init(bucket=email, version=version)
        if err:
            return (None, "storage_init_err")

        return (version, None)  # all good!

    """
    產生帳戶資料
        1. 更新 email 資料到 S3
            檢查 version, 將 email + register_region 覆寫至 S3
        2. 產生 DynamoDB 需要的帳戶資料
    """
    def __generate_account_data(self, email: EmailStr, data: Any, version: str) -> (Union[Any, None], Union[str, None]):
        # 1. 更新 email 資料到 S3
        region = data["region"]
        res, err = self.obj_storage.update(
            bucket=email, version=version, newdata={"region": region})
        if err:
            return (None, "storage_update_err")

        # 2. 產生 DynamoDB 需要的帳戶資料
        data["email"] = email
        account_data = auth_util.gen_account_data(data, "ft")
        return (account_data, None)  # all good!

    """
    將帳戶資料寫入 DB
        1. 將帳戶資料寫入 DynamoDB
            res = { aid, region, email, email2, is_active, role, role_id } = account_data
        2. 錯誤處理..
            a. 先嘗試刪除 DynamoDB
            b. 再嘗試刪除 S3
    """
    def __save_account_data(
        self,
        email: EmailStr,
        account_data: Any,
        auth_db: Any,
        account_db: Any,
    ) -> (Union[Any, None], Union[str, None]):
        # 1. 將帳戶資料寫入 DynamoDB
        res, err = self.auth_repo.create_account(
            auth_db=auth_db, account_db=account_db, email=email, data=account_data)

        # 2. 錯誤處理..
        if err:
            del_res, del_err = self.auth_repo.delete_account_by_email(
                auth_db=auth_db, account_db=account_db, email=email)
            if del_err:
                return (None, "db_del_err")

            del_res, del_err = self.obj_storage.delete(bucket=email)
            if del_err:
                return (None, "storage_del_err")

            return (None, "db_create_err")

        return ({
            "email": res["email"],
            "region": res["region"],
            "role": res["role"],
            "role_id": res["role_id"],
            "created_at": res["created_at"],
        }, None)  # all good!

    """
    驗證登入資訊
        1. 從 DynamoDB (auth) 取得 aid (account_id)
        2. 錯誤處理..
    """
    def __validation(
        self,
        email: EmailStr,
        data: Any,
        current_region: str,
        auth_db: Any,
    ) -> (Union[Any, None], Union[str, None]):
        # 1. 從 DynamoDB (auth) 取得 aid (account_id)
        aid, err = self.auth_repo.authentication(
            db=auth_db, email=email, pw=data["pass"], match_password=auth_util.match_password)

        # 2. 錯誤處理..
        if err == "error_password":
            return (None, "error_password")

        if err == "not_registered":
            email_info, storage_err = self.obj_storage.find(bucket=email)
            if storage_err:
                log.error(f"/login fail, storage_err:{storage_err}")
                return (None, "storage_read_err")

            elif email_info == None:
                return (None, "not_registered")

            # email_info, S3 有，但是這地區的 DB 沒有，有可能在其他地區的 DB
            elif "region" in email_info and email_info["region"] != current_region:
                return (email_info, "wrong_region")

            else:
                # email_info, S3 有:
                # 1. 有 region, 也顯示在該地區 -> S3有, DB沒有。
                # 2. 沒記錄 region
                return (None, "register_fail")

        if err:
            log.error(f"/login authentication fail, err:{err}")
            return (None, "unknow_error")

        return (aid, None)  # all good!

    """
    取得帳戶資料
        從 DynamoDB (accounts) 取得必要的帳戶資料
    """
    def __find_account(self, aid: str, account_db: Any) -> (Union[Any, None], Union[str, None]):
        res, err = self.auth_repo.find_account(db=account_db, aid=aid)
        if err:
            log.error(f"/login find_account fail, err:{err}")
            return (None, "db_read_error")

        res = auth_util.filter_by_keys(
            res, ["email", "region", "role", "role_id", "created_at"])
        return (res, None)

    # TODO: [2]. Close/disable account
    # 新增一個 funcntion 判斷是否允許 login/signup：
    # 1. 是否在三個月內有被停用，
    #       若無，則繼續執行其他程序
    #       若有，且在三個月內，則 API直接回傳 "account_closed"
    #       若有，且超過三個月，則 "請開發者決定" 是否允許重新開啟帳號? 並允許login/signup????? 後面的機制如何?
    # 2. 注意 error handling

    # TODO: 新增 functions 做 API:
    # [1]. Update password
    # [2]. Close/disable account
    # [3]. Forgot password
