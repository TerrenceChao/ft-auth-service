import os
import boto3
import logging as log
from botocore.exceptions import ClientError

log.basicConfig(level=log.INFO)


LOCAL_DB = "http://localhost:8000"
DYNAMODB_URL = os.getenv("DYNAMODB_URL", LOCAL_DB)


def get_db():
    try:
        log.info(f"DYNAMODB_URL:{DYNAMODB_URL}")
        if DYNAMODB_URL == LOCAL_DB:
            dynamodb = boto3.resource('dynamodb', endpoint_url=DYNAMODB_URL)
        else:
            dynamodb = boto3.resource('dynamodb')
            
        yield dynamodb
    except Exception as e:
        log.error(e.__str__())
        raise
    finally:
        pass


def get_client():
    try:
        if DYNAMODB_URL == LOCAL_DB:
            dynamodb_client = boto3.client('dynamodb', endpoint_url=DYNAMODB_URL)
        else:
            dynamodb_client = boto3.client('dynamodb')
            
        yield dynamodb_client
    except Exception as e:
        log.error(e.__str__())
        raise
    finally:
        pass


def client_err_msg(e: ClientError):
    if DYNAMODB_URL == LOCAL_DB:
        if e.response['Error']['Code'] == "ConditionalCheckFailedException":
            return e.response['Error']['Message']
        else:
            return e.__str__()
    else:
        e.msg


def response_success(res):
    if res["ResponseMetadata"] != None and res["ResponseMetadata"]["HTTPStatusCode"] != None:
        return res["ResponseMetadata"]["HTTPStatusCode"] == 200

    log.error(res)
    return False
