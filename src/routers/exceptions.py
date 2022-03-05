from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder


app = FastAPI()


class BusinessEception(Exception):
  def __init__(self, msg: str):
      self.msg = msg

@app.exception_handler(BusinessEception)
def business_exception_handler(request: Request, exc: BusinessEception):
  return JSONResponse(
    status_code=500,
    content={
      "code": 1,
      "msg": exc.msg
    }
  )