from fastapi import status
from fastapi.responses import JSONResponse
from pydantic import BaseModel


def post_success(data=None, msg='ok', code='0'):

    if isinstance(data, BaseModel):
        data = data.dict()

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            'code': code,
            'msg': msg,
            'data': data,
    })

def res_success(data=None, msg='ok', code='0'):

    if isinstance(data, BaseModel):
        data = data.dict()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            'code': code,
            'msg': msg,
            'data': data,
    })


def res_err(data=None, msg='error', code='1'):
    return {
        'code': code,
        'msg': msg,
        'data': data,
    }
