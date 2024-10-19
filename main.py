import os
import asyncio
from mangum import Mangum
from fastapi import FastAPI, Request, APIRouter
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from src.configs import exceptions
from src.infra.resources.manager import resource_manager
from src.configs.adapters import (
    failed_publish_events_dlq,
    failed_subscribed_events_dlq,
)
from src.events.sub.sub_event_manager import (
    retry_pub_event_manager,
    retry_sub_event_manager,
)
from src.routers.v1 import auth, notify
from src.routers.v2 import auth as auth_v2


router_v1 = APIRouter(prefix='/auth/api/v1')
router_v1.include_router(auth.router)
router_v1.include_router(notify.router)

router_v2 = APIRouter(prefix='/auth/api/v2')
router_v2.include_router(auth_v2.router)


STAGE = os.environ.get('STAGE')
root_path = '/' if not STAGE else f'/{STAGE}'
app = FastAPI(title='ForeignTeacher: Auth Service', root_path=root_path)


@app.on_event('startup')
async def startup_event():
    # init global connection pool
    await resource_manager.initial()
    asyncio.create_task(resource_manager.keeping_probe())

    # polling local messages(SQS)
    # asyncio.create_task(failed_publish_events_dlq.subscribe_messages(
    #     retry_pub_event_manager.subscribe_event,
    # ))
    asyncio.create_task(failed_subscribed_events_dlq.subscribe_messages(
        retry_sub_event_manager.subscribe_event,
    ))


@app.on_event('shutdown')
async def shutdown_event():
    # close connection pool
    await resource_manager.close()


exceptions.include_app(app)

app.include_router(router_v1)
app.include_router(router_v2)


class BusinessEception(Exception):
    def __init__(self, term: str):
        self.term = term


@app.exception_handler(BusinessEception)
async def business_exception_handler(request: Request, exc: BusinessEception):
    return JSONResponse(
        status_code=418,
        content={
            'code': 1,
            'msg': f'Oops! {exc.term} is a wrong phrase. Guess again?'
        }
    )


@app.get('/auth-service/{term}')
async def info(term: str):
    if term != 'yolo':
        raise BusinessEception(term=term)
    return {'mention': 'You only live once'}


# Mangum Handler, this is so important
handler = Mangum(app)
