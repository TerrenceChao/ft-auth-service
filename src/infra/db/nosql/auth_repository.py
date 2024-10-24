from typing import Dict, List, Any, Tuple
from decimal import Decimal
from pydantic import EmailStr
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

from .auth_schemas import *
from .ddb_error_handler import *
from ....configs.conf import TABLE_AUTH, TABLE_ACCOUNT, TABLE_ACCOUNT_INDEX, BATCH_LIMIT
from ....configs.constants import DYNAMODB_KEYWORDS
from ....configs.exceptions import *
from ....repositories.auth_repository import IAuthRepository
from ....models.auth_value_objects import UpdatePasswordDTO
import logging as log

log.basicConfig(filemode='w', level=log.INFO)



class AuthRepository(IAuthRepository):
    def __init__(self):
        self.__cls_name = self.__class__.__name__
        self.auth_db = None
        self.account_db = None

    async def get_account_by_email(self, auth_db: Any, account_db: Any, email: EmailStr, fields: List):
        auth_res = None
        acc_res = None
        account = None

        try:
            # 1. get auth
            auth_db = await auth_db.access()
            auth_table = await auth_db.Table(TABLE_AUTH)
            # log.info(auth_table)
            auth_res = await auth_table.get_item(Key={'email': email})
            if not 'Item' in auth_res:
                return None

            # 2. get account by aid
            aid = auth_res['Item']['aid']
            account_db = await account_db.access()
            acc_table = await account_db.Table(TABLE_ACCOUNT)
            # log.info(acc_table)
            
            projection_expression, expression_attr_names = \
                self.__gen_expression_for_get_items(fields)
            if expression_attr_names == {}:
                acc_res = await acc_table.get_item(
                    Key={'aid': aid},
                    ProjectionExpression=projection_expression,
                )
            else:
                acc_res = await acc_table.get_item(
                    Key={'aid': aid},
                    ProjectionExpression=projection_expression,
                    ExpressionAttributeNames=expression_attr_names,
                )

            if not 'Item' in acc_res:
                raise ServerError('there_is_auth_data_but_no_account_data')
                
            return acc_res['Item']
        
        except ClientError as e:
            log.error(f'{self.__cls_name}.get_account_by_email error [read_req_error], \
                email:%s fields:%s, auth_res:%s, acc_res:%s, account:%s, err:%s', 
                email, fields, auth_res, acc_res, account, client_err_msg(e))
            raise Exception('read_req_error')
        
        except ServerError as e:
            log.error(f'{self.__cls_name}.get_account_by_email error [there_is_auth_data_but_no_account_data], \
                email:%s fields:%s, auth_res:%s, acc_res:%s, account:%s, err:%s', 
                email, fields, auth_res, acc_res, account,  e.__str__())
            raise Exception(e.__str__())

        except Exception as e:
            log.error(f'{self.__cls_name}.get_account_by_email error [db_read_error], \
                email:%s fields:%s, auth_res:%s, acc_res:%s, account:%s, err:%s', 
                email, fields, auth_res, acc_res, account, e.__str__())
            raise Exception('db_read_error')

    def __gen_expression_for_get_items(self, fields: List):
        expression_attr_names = {}
        for idx, field in enumerate(fields):
            if field in DYNAMODB_KEYWORDS:
                renamed_field = '#' + field
                expression_attr_names[renamed_field] = field
                fields[idx] = renamed_field
        
        projection_expression = ','.join(fields)
        return projection_expression, expression_attr_names

    async def create_account(self, auth_db: Any, account_db: Any, auth: FTAuth, account: Account) -> Tuple[FTAuth, Account]:
        response = None
        auth_dict: Dict = auth.create_ts().dict()
        account_dict: Dict = account.create_ts().dict()
        account_index: AccountIndex = AccountIndex(
            role_id=auth.role_id,
            aid=auth.aid,
        )
        account_index_dict: Dict = account_index.create_ts().dict()

        try:
            _db = await account_db.access()
            client = _db.meta.client
            response = await client.transact_write_items(
                TransactItems=[
                    {
                        'Put': {
                            'TableName': TABLE_AUTH,
                            'Item': auth_dict,
                            'ConditionExpression': 'attribute_not_exists(email) AND attribute_not_exists(aid)',
                        }
                    },
                    {
                        'Put': {
                            'TableName': TABLE_ACCOUNT,
                            'Item': account_dict,
                            'ConditionExpression': 'attribute_not_exists(aid) AND attribute_not_exists(email)',
                        }
                    },
                    {
                        'Put': {
                            'TableName': TABLE_ACCOUNT_INDEX,
                            'Item': account_index_dict,
                            'ConditionExpression': 'attribute_not_exists(role_id) AND attribute_not_exists(aid)',
                        }
                    },
                ]
            )
            if response_success(response):
                return (auth, account)
            
            raise Exception('insert_req_error')

        except ClientError as e:
            log.error(f'{self.__cls_name}.create_account error [insert_req_error], \
                auth:%s, account:%s, account_index:%s, response:%s, err:%s',
                auth, account, account_index, response, client_err_msg(e))
            raise Exception('insert_req_error')

        except Exception as e:
            log.error(f'{self.__cls_name}.create_account error [db_insert_error], \
                auth:%s, account:%s, account_index:%s, response:%s, err:%s',
                auth, account, account_index, response, e.__str__())
            raise Exception('db_insert_error')


    async def delete_account(self, auth_db: Any, account_db: Any, auth: FTAuth):
        auth_res = None
        response = None
        deleted = False

        try:
            _db = await account_db.access()
            client = _db.meta.client
            response = await client.transact_write_items(
                TransactItems=[
                    {
                        'Delete': {
                            'TableName': TABLE_AUTH,
                            'Key': {'email': auth.email},
                        }
                    },
                    {
                        'Delete': {
                            'TableName': TABLE_ACCOUNT,
                            'Key': {'aid': auth.aid},
                        }
                    },
                    {
                        'Delete': {
                            'TableName': TABLE_ACCOUNT_INDEX,
                            'Key': {'role_id': auth.role_id},
                        }
                    },
                ]
            )
            if response_success(response):
                deleted = True
                
            return deleted

        except ClientError as e:
            log.error(f'{self.__cls_name}.delete_account error [delete_req_error], \
                deleted:%s, email:%s, auth_res:%s, response:%s, err:%s', 
                deleted, auth.email, auth_res, response, client_err_msg(e))
            raise Exception('delete_req_error')

        except Exception as e:
            log.error(f'{self.__cls_name}.delete_account error [db_delete_error], \
                deleted:%s, email:%s, auth_res:%s, response:%s, err:%s', 
                deleted, auth.email, auth_res, response, e.__str__())
            raise Exception('db_delete_error')        


    async def find_account(self, db: Any, aid: Decimal):
        res = None
        result = None
        
        try:
            # 1. find account by aid
            db = await db.access()
            table = await db.Table(TABLE_ACCOUNT)
            # log.info(table)
            res = await table.get_item(Key={'aid': aid})
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


    async def find_account_by_role_id(self, db: Any, role_id: Decimal):
        idx_res = None
        res = None
        result = None
        
        try:
            db = await db.access()
            idx_table = await db.Table(TABLE_ACCOUNT_INDEX)
            # log.info(table)
            idx_res = await idx_table.get_item(Key={'role_id': role_id})
            if idx_res.get('Item', None) != None and 'aid' in idx_res['Item']:
                aid = idx_res['Item']['aid']
                table = await db.Table(TABLE_ACCOUNT)
                res = table.get_item(Key={'aid': aid})
                if res.get('Item', None) != None:
                    result = res['Item']

            return result

        except ClientError as e:
            err = client_err_msg(e)
            log.error(f'{self.__cls_name}.find_account_by_role_id error [read_req_error], \
                role_id:%s idx_res:%s, res:%s, err:%s', \
                    role_id, idx_res, res, err)
            raise Exception('read_req_error')

        except Exception as e:
            err = e.__str__()
            log.error(f'{self.__cls_name}.find_account_by_role_id error [db_read_error], \
                role_id:%s idx_res:%s, res:%s, err:%s', \
                    role_id, idx_res, res, err)
            raise Exception('db_read_error')


    async def find_auth(self, db: Any, email: EmailStr):
        res = None
        result = None

        try:
            # 1. find auth by email only
            db = await db.access()
            table = await db.Table(TABLE_AUTH)
            # log.info(table)
            res = await table.get_item(Key={'email': email})
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


    async def update_password(
        self, db: Any, update_password_params: UpdatePasswordDTO
    ) -> (FTAuth):
        res = None
        try:
            db = await db.access()
            auth_table = await db.Table(TABLE_AUTH)

            res = await auth_table.update_item(
                Key={'email': update_password_params.email},
                UpdateExpression='set pass_salt=:ps, pass_hash=:ph',
                ExpressionAttributeValues={
                    ':ps': update_password_params.pass_salt,
                    ':ph': update_password_params.pass_hash,
                },
                ReturnValues='ALL_NEW',
            )
            if 'Attributes' in res:
                # NOTE: return "role_id" for table: account_indexs
                return FTAuth.parse_obj(res['Attributes'])
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

