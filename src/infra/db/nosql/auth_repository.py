import os
import json
from typing import Dict, List, Any, Optional
from decimal import Decimal
from pydantic import EmailStr
import datetime
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

from ....configs.conf import TABLE_AUTH, TABLE_ACCOUNT, BATCH_LIMIT
from ....configs.database import client_err_msg, response_success
from ....configs.exceptions import *
from ....repositories.auth_repository import IAuthRepository
import logging as log

log.basicConfig(filemode='w', level=log.INFO)

class AuthRepository(IAuthRepository):
    def __init__(self):
        self.__cls_name = self.__class__.__name__

    def get_account_by_email(self, auth_db: Any, account_db: Any, email: EmailStr, fields: List):
        auth_res = None
        acc_res = None
        account = None

        try:
            # 1. get auth
            auth_table = auth_db.Table(TABLE_AUTH)
            log.info(auth_table)
            auth_res = auth_table.get_item(Key={"email": email})
            # 1. fail -> return
            if not "Item" in auth_res:
                return None

            auth = auth_res["Item"]

            # 2. get aid from auth
            aid = auth["aid"]

            # 3. get account by aid
            acc_table = account_db.Table(TABLE_ACCOUNT)
            log.info(acc_table)
            acc_res = acc_table.get_item(Key={"aid": aid})
            # 3. fail -> raise NotFoundError
            if not "Item" in acc_res:
                raise NotFoundError('there_is_auth_data_but_no_account_data')

            account_item = acc_res["Item"]

            # 4. assign fields to result(account)
            account = {}
            for field in fields:
                account[field] = account_item[field]
                
            return account
        
        except ClientError as e:
            log.error(f'{self.__cls_name}.get_account_by_email error [read_req_error], \
                email:%s fields:%s, auth_res:%s, acc_res:%s, account:%s, err:%s', 
                email, fields, auth_res, acc_res, account, client_err_msg(e))
            raise Exception('read_req_error')
        
        except NotFoundError as e:
            log.error(f'{self.__cls_name}.get_account_by_email error [there_is_auth_data_but_no_account_data], \
                email:%s fields:%s, auth_res:%s, acc_res:%s, account:%s, err:%s', 
                email, fields, auth_res, acc_res, account,  e.__str__())
            raise Exception(e.__str__())

        except Exception as e:
            log.error(f'{self.__cls_name}.get_account_by_email error [db_read_error], \
                email:%s fields:%s, auth_res:%s, acc_res:%s, account:%s, err:%s', 
                email, fields, auth_res, acc_res, account, e.__str__())
            raise Exception('db_read_error')

        

    def create_account(self, auth_db: Any, account_db: Any, email: EmailStr, data: Any):
        auth_res = None
        acc_res = None
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
                raise Exception("insert_auth_fail")

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
                raise Exception("insert_account_fail")

            account_item = acc_table.get_item(Key={"aid": data["aid"]})
            account = account_item["Item"]
            
            return account

        except ClientError as e:
            log.error(f'{self.__cls_name}.create_account error [insert_req_error], \
                email:%s auth_res:%s, acc_res:%s, err:%s', 
                email, auth_res, acc_res, client_err_msg(e))
            raise Exception('insert_req_error')

        except Exception as e:
            log.error(f'{self.__cls_name}.create_account error [db_insert_error], \
                email:%s auth_res:%s, acc_res:%s, err:%s', 
                email, auth_res, acc_res, e.__str__())
            raise Exception('db_insert_error')


    def delete_account_by_email(self, auth_db: Any, account_db: Any, email: EmailStr):
        auth_res = None
        acc_del_res = None
        deleted = False

        try:
            # 1. find auth by email
            auth_table = auth_db.Table(TABLE_AUTH)
            log.info(auth_table)
            auth_res = auth_table.get_item(Key={"email": email})
            # 1. fail -> auth not found
            # log.debug("step 1 \b %s", auth_res)
            if not "Item" in auth_res:
                raise Exception("auth_not_found")

            # 2. delete auth by email
            auth = auth_res["Item"]
            auth_del_res = auth_table.delete_item(Key={"email": email})
            # 2. fail -> delete auth fail
            if not response_success(auth_res):
                raise Exception("delete_auth_fail")

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
                raise Exception("delete_account_fail")

            # delete both auth & account
            deleted = True
            return deleted

        except ClientError as e:
            log.error(f'{self.__cls_name}.delete_account_by_email error [delete_req_error], \
                email:%s auth_res:%s, acc_del_res:%s, err:%s', 
                email, auth_res, acc_del_res, client_err_msg(e))
            raise Exception('delete_req_error')

        except Exception as e:
            log.error(f'{self.__cls_name}.delete_account_by_email error [db_delete_error], \
                email:%s auth_res:%s, acc_del_res:%s, err:%s', 
                email, auth_res, acc_del_res, e.__str__())
            raise Exception('db_delete_error')


    def get_auth_by_email(self, db: Any, email: EmailStr):
        res = None
        result = None

        try:
            table = db.Table(TABLE_AUTH)
            log.info(table)
            res = table.get_item(Key={"email": email})
            if 'Item' in res:
                result = res["Item"]
            
            return result

        except ClientError as e:
            log.error(f'{self.__cls_name}.get_auth_by_email error [read_req_error], \
                email:%s res:%s, err:%s', email, res, client_err_msg(e))
            raise Exception('read_req_error')

        except Exception as e:
            log.error(f'{self.__cls_name}.get_auth_by_email error [db_read_error], \
                email:%s res:%s, err:%s', email, res, e.__str__())
            raise Exception('db_read_error')


    def find_account(self, db: Any, aid: Decimal):
        res = None
        result = None
        
        try:
            # 1. find account by aid
            table = db.Table(TABLE_ACCOUNT)
            log.info(table)
            res = table.get_item(Key={"aid": aid})
            if 'Item' in res:
                result = res["Item"]
            
            return result

        except ClientError as e:
            err = client_err_msg(e)
            log.error(f'{self.__cls_name}.find_account error [read_req_error], \
                aid:%s res:%s, err:%s', aid, res, err)
            raise Exception('read_req_error')

        except Exception as e:
            err = e.__str__()
            log.error(f'{self.__cls_name}.find_account error [db_read_error], \
                aid:%s res:%s, err:%s', aid, res, err)
            raise Exception('db_read_error')
