from typing import Any, Union, Tuple
from pydantic import EmailStr
from ..db.nosql.auth_repository import AuthRepository
from ..common import auth_util, email_util
import logging as log

log.basicConfig(level=log.INFO)

class AuthService:
    def __init__(self, auth_repo: AuthRepository) -> None:
        self.auth_repo = auth_repo
        pass


    def send_conform_code_by_email(
        self,
        email: EmailStr,
        confirm_code: str,
        sendby: str,
        auth_db: Any,
        account_db: Any
    ): # -> Tuple[Union[str, None], Union[str, None]]:
        res, err = self.auth_repo.get_account_by_email(
            auth_db=auth_db, 
            account_db=account_db, 
            email=email, 
            fields=["email", "region", "role"]
        )
        
        if sendby == "no_exist" and res == None and err == None:
            email_util.send_conform_code(email=email, confirm_code=confirm_code)
            return ("email_sent", None)

        if res != None:
            return (None, "email_registered")

        return (None, "email_NOT_sent")


    """auth_service: signup
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
        obj_storage: Any
    ): # -> Tuple[Union[Any, None], Union[str, None]]:
        # 1. 檢查 email 有沒註冊過
        email_info_or_version, err = self.__check_if_email_is_registered(email, obj_storage)
        if err:
            return (email_info_or_version, err)

        # 2. 產生帳戶資料
        account_data, err = self.__generate_account_data(data, email, email_info_or_version, obj_storage)
        if err:
            return (None, err)

        # 3. 將帳戶資料寫入 DB
        return self.__save_account_data(auth_db, account_db, email, account_data, obj_storage)
        
        
    """
    登入流程
        1. 驗證登入資訊
        2. 取得帳戶資料
    """
    def login(
        self,
        email: EmailStr,
        data: Any,
        client_region: str,
        auth_db: Any,
        account_db: Any,
        obj_storage: Any
    ): # -> Tuple[Union[Any, None], Union[str, None]]:
        # 1. 驗證登入資訊
        aid, err = self.__verification(data, email, client_region, auth_db, obj_storage)
        if err:
            return (None, err)
        
        # 2. 取得帳戶資料
        return self.__find_account(account_db, aid)


    """
    檢查 email 有沒註冊過
        去 S3 檢查 email 有沒註冊過，若沒有 則先寫入 email + version
    """
    def __check_if_email_is_registered(self, email: EmailStr, obj_storage: Any) -> Tuple[Union[Any, None], Union[str, None]]:
        # Is the email registered with S3?
        email_info, err = obj_storage.find(bucket=email)
        if err:
            return (None, "storage_read_err")
        
        if email_info:
            return (email_info, "registered")
        
        # save email and version into S3 if it's not registered
        version = auth_util.gen_random_string(6)
        version, err = obj_storage.init(bucket=email, version=version)
        if err:
            return (None, "storage_init_err")
        
        return (version, None) # all good!


    """
    產生帳戶資料
        1. 更新 email 資料到 S3
            檢查 version, 將 email + register_region 覆寫至 S3
        2. 產生 DynamoDB 註冊資料
    """
    def __generate_account_data(self, data: Any, email: EmailStr, version: str, obj_storage: Any) -> Tuple[Union[Any, None], Union[str, None]]:
        # 1. 更新 email 資料到 S3
        region = data["region"]
        res, err = obj_storage.update(
            bucket=email, version=version, newdata={"region": region})
        if err:
            return (None, "storage_update_err")
        
        # 2. 產生 DynamoDB 註冊資料
        data["email"] = email
        account_data = auth_util.gen_account_data(data, "ft")
        return (account_data, None) # all good!
        
        
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
        auth_db: Any, 
        account_db: Any, 
        email: EmailStr, 
        account_data: Any, 
        obj_storage: Any
    ) -> Tuple[Union[Any, None], Union[str, None]]:
        # 1. 將帳戶資料寫入 DynamoDB
        res, err = self.auth_repo.create_account(
            auth_db=auth_db, account_db=account_db, email=email, data=account_data)
        
        # 2. 錯誤處理..
        if err:
            del_res, del_err = self.auth_repo.delete_account_by_email(
                auth_db=auth_db, account_db=account_db, email=email)
            if del_err:
                return (None, "db_del_err")

            del_res, del_err = obj_storage.delete(bucket=email)
            if del_err:
                return (None, "storage_del_err")

            return (None, "db_create_err")

        return ({
            "email": res["email"],
            "region": res["region"],
            "role": res["role"],
            "role_id": res["role_id"],
        }, None) # all good!
    
    
    """
    驗證登入資訊
        1. 從 DynamoDB (auth) 取得 aid (account_id)
        2. 錯誤處理..
    """
    def __verification(
        self, 
        data: Any, 
        email: EmailStr,
        client_region: str,
        auth_db: Any,
        obj_storage: Any
    ) -> Tuple[Union[Any, None], Union[str, None]]:
        # 1. 從 DynamoDB (auth) 取得 aid (account_id)
        aid, err = self.auth_repo.authentication(
            db=auth_db, email=email, pw=data["pass"], match_password=auth_util.match_password)
        
        # 2. 錯誤處理..
        if err == "error_password":
            return (None, "error_password")

        if err == "not_registered":
            email_info, storage_err = obj_storage.find(bucket=email)
            if storage_err:
                log.error(f"/login fail, storage_err:{storage_err}")
                return (None, "storage_read_err")
            
            elif email_info == None:
                return (None, "not_registered")

            # email_info, S3 有，但是這地區的 DB 沒有，有可能在其他地區的 DB
            elif "region" in email_info and email_info["region"] != client_region:
                return (email_info, "wrong_region")

            else:
                # email_info, S3 有:
                # 1. 有 region, 也顯示在該地區 -> S3有, DB沒有。
                # 2. 沒記錄 region
                return (None, "register_fail")

        if err:
            log.error(f"/login authentication fail, err:{err}")
            return (None, "unknow_error")
        
        return (aid, None) # all good!
    
    
    """
    取得帳戶資料
        從 DynamoDB (account) 取得必要的帳戶資料
    """
    def __find_account(self, account_db: Any, aid: str) -> Tuple[Union[Any, None], Union[str, None]]:
        res, err = self.auth_repo.find_account(db=account_db, aid=aid)
        if err:
            log.error(f"/login find_account fail, err:{err}")
            return (None, "db_read_error")
        
        res = auth_util.filter_by_keys(res, ["email", "region", "role", "role_id"]) 
        return (res, None)


