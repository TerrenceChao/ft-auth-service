import json
from fastapi import APIRouter, Request
from ..sub_event_manager import sub_remote_event_manager
import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


router = APIRouter(
    prefix='/subscribe',
    tags=['subscribe'],
    responses={404: {'description': 'Not found'}},
)

'''
{
    "version": "0",
    "id": "91bb96ab-1bf4-472e-e92d-c80ab851ad4c",
    "detail-type": "TestEvent",
    "source": "ft.test",
    "account": "549734764220",
    "time": "2024-10-18T10:45:39Z",
    "region": "ap-northeast-1",
    "resources": [],
    "detail": {
        "event_id": 7252993067811254,
        "event_type": "user_registration",
        "metadata": {
            "auth": {
                "created_at": 0,
                "updated_at": 0,
                "email": "user@example.com",
                "aid": 100,
                "role_id": 100,
                "pass_hash": "The msg comes from Tokyo",
                "pass_salt": "The msg comes from Tokyo",
                "sso_id": "string"
            },
            "account": {
                "created_at": 0,
                "updated_at": 0,
                "aid": 100,
                "region": "jp",
                "email": "user@example.com",
                "email2": "user@example.com",
                "is_active": true,
                "role": "string",
                "role_id": 100,
                "account_type": "ft"
            }
        },
        "retry": 0,
        "region": "ap-northeast-1"
    }
}
'''
@router.post('/remote-events')
async def receive_remote_event(request: Request):
    event = await request.json()  # 獲取 JSON 請求體
    log.info('Received Remote Event: %s', json.dumps(event, indent=2))  # 打印事件內容

    # 在這裡處理事件邏輯
    event_detail = event.get('detail', None)
    if not event_detail:
        return {
            'message': 'Remote Event detail is empty!',
        }

    await sub_remote_event_manager.subscribe_event(event_detail)
    return {
        'message': 'Remote Event received successfully!',
        'event': event,
    }


# @router.post('/local-events')
# async def receive_local_event(request: Request):
#     event = await request.json()  # 獲取 JSON 請求體
#     log.info('Received Local Event: %s', json.dumps(event, indent=2))  # 打印事件內容

#     # 在這裡處理事件邏輯
#     event_detail = event.get('detail', None)
#     if not event_detail:
#         return {
#             'message': 'Local Event detail is empty!',
#         }
    
#     return {
#         'message': 'Local Event received successfully!',
#         'event': event,
#     }