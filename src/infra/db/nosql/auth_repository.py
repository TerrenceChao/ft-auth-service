import os
import json

from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
from pydantic import EmailStr, BaseModel
import datetime
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

from ....configs.conf import TABLE_AUTH, TABLE_ACCOUNT, BATCH_LIMIT
from ....configs.database import client_err_msg, response_success
from ....configs.exceptions import *
from ....repositories.auth_repository import IAuthRepository, UpdatePasswordParams
import logging as log
from src.infra.utils import auth_util 

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
            # log.info(auth_table)
            auth_res = auth_table.get_item(Key={'email': email})
            if not 'Item' in auth_res:
                return None

            # 2. get account by aid
            aid = auth_res['Item']['aid']
            acc_table = account_db.Table(TABLE_ACCOUNT)
            # log.info(acc_table)
            acc_res = acc_table.get_item(
                Key={'aid': aid},
                ProjectionExpression=','.join(fields)
            )
            if not 'Item' in acc_res:
                raise NotFoundError('there_is_auth_data_but_no_account_data')
                
            return acc_res['Item']
        
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
            # log.info(auth_table)
            auth_res = auth_table.put_item(
                Item={
                    'email': email,
                    'aid': data['aid'],
                    'pass_hash': data['pass_hash'],
                    'pass_salt': data['pass_salt'],
                },
                ConditionExpression='attribute_not_exists(email) AND attribute_not_exists(aid)'
            )
            # 1. fail -> return
            if not response_success(auth_res):
                raise Exception('insert_auth_fail')

            # 2. create account
            acc_table = account_db.Table(TABLE_ACCOUNT)
            # log.info(acc_table)
            acc_res = acc_table.put_item(
                Item={
                    'aid': data['aid'],
                    'region': data['region'],
                    'email': email,
                    'email2': None,
                    'is_active': True,
                    'role': data['role'],
                    'role_id': data['role_id'],
                    'type': data['type'], # account_type: ft, fb, or google
                    'created_at': data['created_at'],
                },
                ConditionExpression='attribute_not_exists(aid) AND attribute_not_exists(email)'
            )

            if not response_success(acc_res):
                raise Exception('insert_account_fail')

            account_item = acc_table.get_item(Key={'aid': data['aid']})
            account = account_item['Item']
            
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
            # log.info(auth_table)
            auth_res = auth_table.get_item(Key={'email': email})
            if not 'Item' in auth_res:
                return deleted # False

            # 2. delete auth by email
            auth_del_res = auth_table.delete_item(Key={'email': email})
            if not response_success(auth_del_res):
                raise Exception('delete_auth_fail')

            # 3. delete account by aid
            aid = auth_res['Item']['aid']
            acc_table = account_db.Table(TABLE_ACCOUNT)
            # log.info(acc_table)
            acc_del_res = acc_table.delete_item(Key={'aid': aid})
            if not response_success(acc_del_res):
                raise Exception('delete_account_fail')

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


    def find_account(self, db: Any, aid: Decimal):
        res = None
        result = None
        
        try:
            # 1. find account by aid
            table = db.Table(TABLE_ACCOUNT)
            # log.info(table)
            res = table.get_item(Key={'aid': aid})
            if 'Item' in res:
                result = res['Item']
            
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


    def find_auth(self, db: Any, email: EmailStr):
        res = None
        result = None

        try:
            # 1. find auth by email only
            table = db.Table(TABLE_AUTH)
            # log.info(table)
            res = table.get_item(Key={'email': email})
            if 'Item' in res:
                result = res['Item']
            
            return result

        except ClientError as e:
            err = client_err_msg(e)
            log.error(f'{self.__cls_name}.find_auth error [read_req_error], \
                email:%s res:%s, err:%s', email, res, err)
            raise Exception('read_req_error')

        except Exception as e:
            err = e.__str__()
            log.error(f'{self.__cls_name}.find_auth error [db_read_error], \
                email:%s res:%s, err:%s', email, res, err)
            raise Exception('db_read_error')


    def update_password(
        self, db: Any, update_password_params: UpdatePasswordParams
    ) -> (bool):
        res = None
        try:
            auth_table = db.Table(TABLE_AUTH)

            res = auth_table.update_item(
                Key={'email': update_password_params.email},
                UpdateExpression='set pass_salt=:ps, pass_hash=:ph',
                ExpressionAttributeValues={
                    ':ps': update_password_params.pass_salt,
                    ':ph': update_password_params.pass_hash,
                },
                ReturnValues='UPDATED_NEW',
            )
            if 'Attributes' in res:
                return True
            else:
                raise Exception('update_password_fail')
    
        except ClientError as e:
            err = client_err_msg(e)
            log.error(f'{self.__cls_name}.update_password error [update_req_error], \
                update_password_params:%s, res:%s, err:%s', update_password_params, res, err)
            raise Exception('update_req_error')

        except Exception as e:
            err = e.__str__()
            log.error(f'{self.__cls_name}.update_password error [update_password_fail], \
                update_password_params:%s, res:%s, err:%s', update_password_params, res, err)
            raise Exception('update_password_fail')

