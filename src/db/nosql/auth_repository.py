import os
import json
from typing import Dict, List, Any, Optional
import logging
import datetime
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

from .database import client_err_msg, response_success
from ...repositories.auth_repository import IAuthRepository


log = logging.getLogger()
log.setLevel(logging.INFO)


TABLE_AUTH = os.getenv("TABLE_AUTH", "auth")
TABLE_ACCOUNT = os.getenv("TABLE_ACCOUNT", "accounts")
BATCH_LIMIT = int(os.getenv("BATCH_LIMIT", "25"))


class AuthRepository(IAuthRepository):
  def __init__(self):
    pass
    
  def get_account_by_email(self, auth_db: Any, account_db: Any, email: str, fields: List):
    err_msg: str = None
    account = None

    try:
      # 1. get auth
      auth_table = auth_db.Table(TABLE_AUTH)
      log.info(auth_table, auth_db)
      auth_res = auth_table.get_item(Key={"email": email})
      # 1. fail -> return
      if not "Item" in auth_res:
        return account, err_msg # err = None

      auth = auth_res["Item"]


      # 2. get aid from auth
      aid = auth["aid"]
    
      # 3. get account by aid
      acc_table = account_db.Table(TABLE_ACCOUNT)
      log.info(acc_table, account_db)
      acc_res = acc_table.get_item(Key={"aid": aid})
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
  
  
  def create_account(self, auth_db: Any, account_db: Any, email: str, data: Any):
    err_msg: str = None
    account = None
    
    try:
      # 1. create auth
      auth_table = auth_db.Table(TABLE_AUTH)
      log.info(auth_table, auth_db)
      auth_res = auth_table.put_item(
        Item={
          "email": email,
          "aid": data["aid"],
          "pass_hash": data["pass_hash"],
          "pass_salt": data["pass_salt"],
        }
      )
      # 1. fail -> return
      if not response_success(auth_res):
        return account, "insert_auth_fail"
      

      # 2. create account
      acc_table = account_db.Table(TABLE_ACCOUNT)
      log.info(acc_table, account_db)
      acc_res = acc_table.put_item(
        Item={
          "aid": data["aid"],
          "region": data["region"],
          "email": email,
          "email2": None,
          "is_active": True,
          "role": data["role"],
          "role_id": data["role_id"],
        }
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
  

  def delete_account_by_email(self, auth_db: Any, account_db: Any, email: str):
    err_msg: str = None
    deleted = False
    
    try:
      # 1. find auth by email
      auth_table = auth_db.Table(TABLE_AUTH)
      log.info(auth_table, auth_db)
      auth_res = auth_table.get_item(Key={"email": email})
      # 1. fail -> auth not found
      print("step 1 \b", auth_res)
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
      log.info(acc_table, account_db)
      acc_del_res = acc_table.delete_item(Key={"aid": aid})
      
      # 4. delete account fail -> update acccount(is_active = False)
      if not response_success(acc_del_res):
        # TODO: 因 account 刪除失敗，將 is_active 設定為 False
        res = acc_table.update_item(
          Key={"aid": aid},
          UpdateExpression="set #is_active = :is_active",
          ExpressionAttributeNames={ "#is_active": "is_active" },
          ExpressionAttributeValues={ ":is_active": False },
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

  
  def authentication(self, db: Any, email: str, pw: str, hash_func: Any):
    err_msg: str = None
    result = None
    
    try:
      # 1. find auth by email
      table = db.Table(TABLE_AUTH)
      log.info(table, db)
      res = table.get_item(Key={"email": email})
      print("step 1", res)
      
      # TODO: check not_registered
      #1. not_registered
      if not "Item" in res:
        print("step 1 not_registered")
        return result, "not_registered"
      
      auth = res["Item"]
      print("step 2", auth)
      
      # 2. get pass info
      pass_hash = auth["pass_hash"]
      pass_salt = auth["pass_salt"]
      
      # TODO: error_password
      # 3. validation password by hash_func
      if not hash_func(hash=pass_hash, pw=pw, salt=pass_salt):
        return result, "error_password"
      
      
      # 4. return aid
      result = auth["aid"]
      
    except ClientError as e:
      err_msg = client_err_msg(e)
          
    except Exception as e:
      err_msg = e.__str__()

    return result, err_msg
  

  def find_account(self, db: Any, aid: int):
    err_msg: str = None
    result = None
    
    try:
      # 1. find account by aid
      table = db.Table(TABLE_ACCOUNT)
      log.info(table, db)
      res = table.get_item(Key={"aid": aid})
      result = res["Item"]
      
    except ClientError as e:
      err_msg = client_err_msg(e)
          
    except Exception as e:
      err_msg = e.__str__()

    return result, err_msg
  