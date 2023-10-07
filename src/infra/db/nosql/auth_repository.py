import os
import json
import hashlib
from typing import Dict, List, Any, Optional
from decimal import Decimal
from pydantic import EmailStr
import datetime
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

from ....configs.conf import TABLE_AUTH, TABLE_ACCOUNT, BATCH_LIMIT
from ....configs.database import client_err_msg, response_success
from ....repositories.auth_repository import IAuthRepository
import logging as log
from src.infra.utils import auth_util 

log.basicConfig(filemode='w', level=log.INFO)

class AuthRepository(IAuthRepository):
    def __init__(self):
        pass

    def get_account_by_email(self, auth_db: Any, account_db: Any, email: EmailStr, fields: List):
        err_msg: str = None
        account = None

        try:
            # 1. get auth
            auth_table = auth_db.Table(TABLE_AUTH)
            log.info(auth_table)
            auth_res = auth_table.get_item(Key={"email": email})
            # 1. fail -> return
            if not "Item" in auth_res:
                return account, None  # err = None

            auth = auth_res["Item"]

            # 2. get aid from auth
            aid = auth["aid"]

            # 3. get account by aid
            acc_table = account_db.Table(TABLE_ACCOUNT)
            log.info(acc_table)
            acc_res = acc_table.get_item(Key={"aid": aid})
            if not "Item" in acc_res:
                return account, "auth_data_without_account"  # err = None

            account_item = acc_res["Item"]

            # 4. assign fields to result(account)
            account = {}
            for field in fields:
                account[field] = account_item[field]

        except ClientError as e:
            err_msg = client_err_msg(e)

        except Exception as e:
            err_msg = e.__str__()

        return account, err_msg

    def create_account(self, auth_db: Any, account_db: Any, email: EmailStr, data: Any):
        err_msg: str = None
        account = None

        try:
            # 1. create auth
            auth_table = auth_db.Table(TABLE_AUTH)
            log.info(auth_table)
            auth_res = auth_table.put_item(
                Item={
                    "email": email,
                    "aid": data["aid"],
                    "pass_hash": data["pass_hash"],
                    "pass_salt": data["pass_salt"],
                },
                ConditionExpression='attribute_not_exists(email) AND attribute_not_exists(aid)'
            )
            # 1. fail -> return
            if not response_success(auth_res):
                return account, "insert_auth_fail"

            # 2. create account
            acc_table = account_db.Table(TABLE_ACCOUNT)
            log.info(acc_table)
            acc_res = acc_table.put_item(
                Item={
                    "aid": data["aid"],
                    "region": data["region"],
                    "email": email,
                    "email2": None,
                    "is_active": True,
                    "role": data["role"],
                    "role_id": data["role_id"],
                    "type": data["type"], # account_type: ft, fb, or google
                    "created_at": data["created_at"],
                },
                ConditionExpression='attribute_not_exists(aid) AND attribute_not_exists(email)'
            )

            if not response_success(acc_res):
                return account, "insert_account_fail"

            account_item = acc_table.get_item(Key={"aid": data["aid"]})
            account = account_item["Item"]

        except ClientError as e:
            err_msg = client_err_msg(e)

        except Exception as e:
            err_msg = e.__str__()

        return account, err_msg

    def delete_account_by_email(self, auth_db: Any, account_db: Any, email: EmailStr):
        err_msg: str = None
        deleted = False

        try:
            # 1. find auth by email
            auth_table = auth_db.Table(TABLE_AUTH)
            log.info(auth_table)
            auth_res = auth_table.get_item(Key={"email": email})
            # 1. fail -> auth not found
            # log.debug("step 1 \b %s", auth_res)
            if not "Item" in auth_res:
                return deleted, "auth_not_found"

            # 2. delete auth by email
            auth = auth_res["Item"]
            auth_del_res = auth_table.delete_item(Key={"email": email})
            # 2. fail -> delete auth fail
            if not response_success(auth_res):
                return deleted, "delete_auth_fail"

            # 3. get aid from auth
            aid = auth["aid"]

            # 4. delete account by aid
            acc_table = account_db.Table(TABLE_ACCOUNT)
            log.info(acc_table)
            acc_del_res = acc_table.delete_item(Key={"aid": aid})

            # 4. delete account fail -> update acccount(is_active = False)
            if not response_success(acc_del_res):
                # TODO: 因 account 刪除失敗，將 is_active 設定為 False
                res = acc_table.update_item(
                    Key={"aid": aid},
                    UpdateExpression="set #is_active = :is_active",
                    ExpressionAttributeNames={"#is_active": "is_active"},
                    ExpressionAttributeValues={":is_active": False},
                    ReturnValues="UPDATED_NEW"
                )
                return deleted, "delete_account_fail"

            # delete both auth & account
            deleted = True

        except ClientError as e:
            err_msg = client_err_msg(e)

        except Exception as e:
            err_msg = e.__str__()

        return deleted, err_msg

    def authentication(self, db: Any, email: EmailStr, pw: str, match_password: Any):
        err_msg: str = None
        result = None

        try:
            # 1. find auth by email
            table = db.Table(TABLE_AUTH)
            log.info(table)
            res = table.get_item(Key={"email": email})
            # log.debug("step 1 %s", res)

            # TODO: check not_registered
            # 1. not_registered
            if not "Item" in res:
                # log.debug("step 1 not_registered")
                return result, "not_registered"

            auth = res["Item"]
            # log.debug("step 2 %s", auth)

            # 2. get pass info
            pass_hash = auth["pass_hash"]
            pass_salt = auth["pass_salt"]

            # TODO: error_password
            # 3. validation password by match_password
            if not match_password(pass_hash=pass_hash, pw=pw, pass_salt=pass_salt):
                return result, "error_password"

            # log.debug("step 3 %s", type(auth["aid"]))
            # 4. return aid
            result = auth["aid"]

        except ClientError as e:
            err_msg = client_err_msg(e)

        except Exception as e:
            err_msg = e.__str__()

        return result, err_msg

    def find_account(self, db: Any, aid: Decimal):
        err_msg: str = None
        result = None

        try:
            # 1. find account by aid
            table = db.Table(TABLE_ACCOUNT)
            log.info(table)
            res = table.get_item(Key={"aid": aid})
            result = res["Item"]

        except ClientError as e:
            err_msg = client_err_msg(e)

        except Exception as e:
            err_msg = e.__str__()

        return result, err_msg

    def update_password(self, db: Any, aid: Decimal, new_pw: str, origin_pw: Optional[str] = None) -> Optional[str]:
        err_msg: Optional[str] = None

        pass_salt = auth_util.gen_random_string(12)
        password_data = str(new_pw + pass_salt).encode("utf-8")
        pass_hash = hashlib.sha224(password_data).hexdigest()

        try:
            #1. find auth by aid
            auth_table = db.Table(TABLE_AUTH)
            if origin_pw is not None and not _is_pw_valid(table=auth_table, aid=aid, pw=origin_pw):
                return "error_password"

            auth_table.update_item(
                Key={'aid': aid},
                UpdateExpression="set pass_salt=:ps, pass_hash=:ph",
                ExpressionAttributeValues={
                    ':ps': pass_salt, ':ph': pass_hash},
                ReturnValues="UPDATED_NEW")
        except ClientError as e:
            err_msg = client_err_msg(e)

        except Exception as e:
            err_msg = e.__str__()

        return err_msg

def _is_pw_valid(table: Any, aid: str, pw: str) -> bool:
        res = table.get_item(Key={"aid": aid})

        if not "Item" in res:
            return False

        auth = res["Item"]

        pass_hash = auth["pass_hash"]
        pass_salt = auth["pass_salt"]

        if not auth_util.match_password(pass_hash=pass_hash, pw=pw, pass_salt=pass_salt):
            return False
        
        return True
