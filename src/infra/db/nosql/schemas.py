from typing import List, Optional
from pydantic import BaseModel, EmailStr
from .public_schemas import BaseEntity

class BaseAuth(BaseEntity):
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


class Account(BaseEntity):
    aid: int
    region: str
    email: EmailStr
    email2: Optional[EmailStr] = None
    # TODO: [2]. Close/disable account
    # 考慮三個月內 同用戶無法註冊/登入的機制；是否需要加上 [is_active = False狀態] 的 timestamp?
    is_active: bool = True # True: 開啟帳號, False: 關閉帳號
    role: str
    role_id: Optional[int] = None




# request
class FTUser(BaseModel):
    email: EmailStr
    # user's { 'region/current_region', 'role', pass } 透過 pubkey 編碼取得，可解密
    meta: Optional[str] = None
    pubkey: Optional[str] = None
    confirm_code: Optional[str] = None


# response
class User(BaseModel):
    email: EmailStr
    region: Optional[str] = None  # 在哪裡找資料庫 很重要
    current_region: Optional[str] = None  # 訊息發送到哪裡 很重要
    role: str
    role_id: int
    token: str

    # TODO: def cache(): ...
