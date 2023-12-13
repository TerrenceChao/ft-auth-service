
import requests
import json
from fastapi.responses import RedirectResponse
from typing import List, Optional
from pydantic import BaseModel

from src.models.sso_api import GeneralUserInfo
from src.infra.utils.url_util import parse_url

CLIENT_ID = '652252489794-hf50ke4tqvp39hf27tbpfi06evsttuh8.apps.googleusercontent.com'
CLIENT_SECRET = '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'

class GoogleUserInfoResponse(BaseModel):
    sub: str
    email: str

class OauthResponse(BaseModel):
    id_token: str

class GoogleLoginRepository:
    def __init__(self) -> None:
        self.client_id = CLIENT_ID
        self.client_secret = CLIENT_SECRET
        self.auth_uri = 'https://accounts.google.com/o/oauth2/auth?'
        self.token_uri = 'https://oauth2.googleapis.com/token?'
        self.redirect_uri = 'http://localhost:8002/auth/api/v2/auth-nosql/google/login'

    def auth(self, state_payload: str) -> RedirectResponse:
        payload = {
            'client_id': self.client_id,
            'response_type': 'code',
            'scope': 'profile openid email',
            'redirect_uri': self.redirect_uri,
            'state': state_payload,
        }
        return RedirectResponse(parse_url(self.auth_uri, payload))
        
    def token(self, code: str) -> OauthResponse:
        payload = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': self.redirect_uri,
            'grant_type': 'authorization_code'
        }
        resp = requests.post(
            url=self.token_uri,
            data=payload
        )
        data = resp.json()
        return OauthResponse.parse_obj(data)
        

    def user_info(self, id_token: str) -> GoogleUserInfoResponse:
        payload = {
            'id_token': id_token
        }
        path = 'https://oauth2.googleapis.com/tokeninfo?'

        resp = requests.get(
            path,
            params=payload,
        )
        data = resp.json()
        return GoogleUserInfoResponse.parse_obj(data)

    def google_user_info_to_general(self, google_user_info: GoogleUserInfoResponse) -> GeneralUserInfo:
        return GeneralUserInfo(
            id=google_user_info.sub,
            email=google_user_info.email,
        )
