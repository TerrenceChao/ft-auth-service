import os
import boto3
import logging
from botocore.exceptions import ClientError


log = logging.getLogger()
log.setLevel(logging.ERROR)


DYNAMODB_URL = os.getenv("DYNAMODB_URL", "http://localhost:8000")


def get_db():
    dynamodb = boto3.resource('dynamodb', endpoint_url=DYNAMODB_URL)
    try:
        yield dynamodb
    except Exception as e:
        log.error(e.__str__())
        raise
    finally:
        pass


def get_client():
    dynamodb_client = boto3.client('dynamodb', endpoint_url=DYNAMODB_URL)
    try:
        yield dynamodb_client
    except Exception as e:
        log.error(e.__str__())
        raise
    finally:
        pass


def client_err_msg(e: ClientError):
    if e.response['Error']['Code'] == "ConditionalCheckFailedException":
        return e.response['Error']['Message']
    else:
        return e.__str__()


def response_success(res):
    if res["ResponseMetadata"] != None and res["ResponseMetadata"]["HTTPStatusCode"] != None:
        return res["ResponseMetadata"]["HTTPStatusCode"] == 200

    # log.error(res)
    print(res)
    return False
