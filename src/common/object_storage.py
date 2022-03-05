import logging


log = logging.getLogger()
log.setLevel(logging.INFO)


def init_global_storage(bucket, data):
  version = 1
  return version, None

def update_global_storage(bucket, olddata, newdata):
  return True, None

def delete_global_storage(bucket):
  return True, None

def find_global_storage(bucket):
  return {
    "email": "abc@gmail.com",
    "region": "jp",
  }, None