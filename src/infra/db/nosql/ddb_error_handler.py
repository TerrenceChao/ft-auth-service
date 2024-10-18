from botocore.exceptions import ClientError
import logging as log

log.basicConfig(filemode='w', level=log.INFO)


def client_err_msg(e: ClientError):
    if e.response['Error']['Message']:
        return e.response['Error']['Message']
    else:
        return e.__str__()


def response_success(res):
    if res["ResponseMetadata"] != None and res["ResponseMetadata"]["HTTPStatusCode"] != None:
        return res["ResponseMetadata"]["HTTPStatusCode"] == 200

    log.error(res)
    return False
