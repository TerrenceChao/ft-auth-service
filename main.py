import os
import json
from sys import prefix
from mangum import Mangum
from typing import Optional, List, Dict
from fastapi import FastAPI, Request, \
    Cookie, Header, Path, Query, Body, Form, \
    File, UploadFile, status, \
    HTTPException, \
    Depends, \
    APIRouter
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from src.configs import exceptions
from src.routers.v1 import auth
from src.routers.v2 import auth as auth_v2

# TODO: 在 src/routers/v2/auth.py 新增 routers 做 API:
# [1]. Update password
# [2]. Close/disable account
# [3]. Forgot password

router_v1 = APIRouter(prefix="/auth/api/v1")
router_v1.include_router(auth.router)

router_v2 = APIRouter(prefix='/auth/api/v2')
router_v2.include_router(auth_v2.router)

STAGE = os.environ.get('STAGE')
root_path = '/' if not STAGE else f'/{STAGE}'
app = FastAPI(title="ForeignTeacher: Auth Service", root_path=root_path)
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
            "code": 1,
            "msg": f"Oops! {exc.term} is a wrong phrase. Guess again?"
        }
    )


@app.get("/auth-service/{term}")
async def info(term: str):
    if term != "yolo":
        raise BusinessEception(term=term)
    return {"mention": "You only live once"}


# Mangum Handler, this is so important
handler = Mangum(app)
