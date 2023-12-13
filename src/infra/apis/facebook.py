import requests
import json
from fastapi.responses import RedirectResponse
from typing import List, Optional
from pydantic import BaseModel

from src.models.sso_api import GeneralUserInfo
from src.infra.utils.url_util import parse_url
from src.configs.conf import FACEBOOK_APP_ID, FACEBOOK_APP_SECRET, FACEBOOK_REDIRECT_URI

FACEBOOK_APP_VERSION = 'v18.0'
FACEBOOK_GRAPH_URL = f'https://graph.facebook.com/{FACEBOOK_APP_VERSION}'
FACEBOOK_URL = f'https://www.facebook.com/{FACEBOOK_APP_VERSION}'

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
        self.redircet_uri = FACEBOOK_REDIRECT_URI
    
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
                'redirect_uri': self.redircet_uri,
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

    def dialog(self, state_payload: str) -> str:
        payload = {
            'client_id': self.facebook_app_id,
            'redirect_uri': self.redircet_uri,
            'state': state_payload,
        }
        path = f'{FACEBOOK_URL}/dialog/oauth?'
        full_path = parse_url(path, payload)
        resp = RedirectResponse(full_path)
        return resp

    def fb_user_info_to_general(self, fb_user_info: GetUserInfoResponse) -> GeneralUserInfo:
        return GeneralUserInfo(
            id=fb_user_info.id,
            email=fb_user_info.email,
        )
