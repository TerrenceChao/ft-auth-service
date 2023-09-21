import boto3

s3_resource = boto3.resource("s3")


def get_s3_resource():
    return s3_resource
