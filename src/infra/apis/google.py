
from pydantic import BaseModel

from src.configs.conf import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI
from src.models.sso_api import GeneralUserInfo, RedirectUrl
from src.infra.utils.url_util import parse_url
from ..client.request_client_adapter import RequestClientAdapter

class GoogleUserInfoResponse(BaseModel):
    sub: str
    email: str

class OauthResponse(BaseModel):
    id_token: str

class GoogleLoginRepository:
    def __init__(self, request: RequestClientAdapter) -> None:
        self.client_id = GOOGLE_CLIENT_ID
        self.client_secret = GOOGLE_CLIENT_SECRET
        self.redirect_uri = GOOGLE_REDIRECT_URI
        self.request = request

    def auth(self, state_payload: str) -> RedirectUrl:
        payload = {
            'client_id': self.client_id,
            'response_type': 'code',
            'scope': 'profile openid email',
            'redirect_uri': self.redirect_uri,
            'state': state_payload,
        }
        full_path = parse_url('https://accounts.google.com/o/oauth2/auth?', payload)
        return RedirectUrl(redirect_url=full_path)
        
    async def token(self, code: str) -> OauthResponse:
        payload = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': self.redirect_uri,
            'grant_type': 'authorization_code'
        }
        data = await self.request.simple_post(
            url='https://oauth2.googleapis.com/token?',
            json=payload # TODO: check data=payload or json=payload
        )
        return OauthResponse.parse_obj(data)
        

    async def user_info(self, id_token: str) -> GoogleUserInfoResponse:
        payload = {
            'id_token': id_token
        }
        data = await self.request.simple_get(
            url='https://oauth2.googleapis.com/tokeninfo?',
            params=payload,
        )
        return GoogleUserInfoResponse.parse_obj(data)

    def google_user_info_to_general(self, google_user_info: GoogleUserInfoResponse) -> GeneralUserInfo:
        return GeneralUserInfo(
            id=google_user_info.sub,
            email=google_user_info.email,
        )
