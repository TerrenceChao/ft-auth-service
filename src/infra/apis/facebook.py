import requests
import json
from fastapi.responses import RedirectResponse
from typing import List, Optional
from pydantic import BaseModel

from src.repositories.third_party_login_repository import IThirdPartyLogin, ThirdPartyUserInfo
from src.infra.utils.url_util import parse_url
FACEBOOK_APP_ID = '829288179205024'
FACEBOOK_APP_SECRET = '0de1fb7a89306e010a538ef8e9da0728'

FACEBOOK_APP_VERSION = 'v18.0'
FACEBOOK_GRAPH_URL = f'https://graph.facebook.com/{FACEBOOK_APP_VERSION}'
FACEBOOK_URL = f'https://www.facebook.com/{FACEBOOK_APP_VERSION}'

REDIRECT_URL = f'https://localhost:3002/api/login'

class StatePayload(BaseModel):
    verified_code: str = 'verified_code'
    role: str
    region: str

class GetUserInfoResponse(BaseModel):
    id: str
    email: str

class OauthResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class FBLoginRepository:
    def __init__(self) -> None:
        self.facebook_app_id = FACEBOOK_APP_ID
        self.facebook_app_secret = FACEBOOK_APP_SECRET
        self.facebook_app_version = FACEBOOK_APP_VERSION
        self.facebook_url = f'https://graph.facebook.com/{FACEBOOK_APP_VERSION}'
    
    def get_user_info(self, access_token: str, fields: Optional[List[str]] = None) -> GetUserInfoResponse:
        if not fields:
            fields = ['email', 'id', 'name']
        api_endpoint = f'{FACEBOOK_GRAPH_URL}/me'
        params = {
            'access_token': access_token,
            'fields': ','.join(fields)
        }
        resp = requests.get(url=api_endpoint, params=params)
        data = resp.json()

        try:
            user_info = GetUserInfoResponse.parse_obj(data)
        except:
            user_info = None
        
        return user_info

    def oauth(self, code) -> str:
        payload = {
                'client_id': self.facebook_app_id,
                'client_secret': self.facebook_app_secret,
                'code': code,
                'redirect_uri': 'http://localhost:8002/auth/api/v2/auth-nosql/fb/login',
            }
        resp = requests.get(
            f'{FACEBOOK_GRAPH_URL}/oauth/access_token?',
            params=payload,
        )
        data = resp.json()

        try:
            oauth_data = OauthResponse.parse_obj(data)
        except:
            oauth_data = None

        return oauth_data 

    def dialog(self, role: str, region: str) -> str:
        state = StatePayload(role=role, region=region)
        payload = {
            'client_id': self.facebook_app_id,
            'redirect_uri': 'http://localhost:8002/auth/api/v2/auth-nosql/fb/login',
            'state': json.dumps(state.dict()),
        }
        path = f'{FACEBOOK_URL}/dialog/oauth?'
        full_path = parse_url(path, payload)
        print('='*20)
        print(full_path)
        resp = RedirectResponse(full_path)
        return resp

