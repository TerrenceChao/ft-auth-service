from typing import List, Optional
from pydantic import BaseModel, EmailStr


class BaseAuth(BaseModel):
  email: EmailStr
  aid: Optional[int] = None

  
class FTAuth(BaseAuth):
  pass_hash: Optional[str] = None
  pass_salt: Optional[str] = None


# TODO:
class FacebookAuth(BaseAuth):
  pass


# TODO:
class GoogleAuth(BaseAuth):
  pass


class Account(BaseModel):
  aid: Optional[int] = None
  region: str
  email: EmailStr
  email2: Optional[EmailStr] = None
  in_active: bool = True
  role: str
  role_id: Optional[int] = None
  auth: BaseAuth
  

## request
class FTUser(BaseModel):
  email: EmailStr
  meta: Optional[str] = None # user's { "region/current_region", "role", pass } 透過 pubkey 編碼取得，可解密
  pubkey: Optional[str] = None
  confirm_code: Optional[str] = None
  

## response
class User(BaseModel):
  email: EmailStr
  region: Optional[str] = None # 在哪裡找資料庫 很重要
  current_region: Optional[str] = None  # 訊息發送到哪裡 很重要
  role: str
  role_id: int
  token: str
  
  # TODO: def cache(): ...