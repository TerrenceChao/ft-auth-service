import os

LOCAL_REGION = os.getenv("LOCAL_REGION", "ap-northeast-1")


# cache conf
TOKEN_EXPIRE_TIME = int(os.getenv('TOKEN_EXPIRE_TIME', 60 * 60 * 24 * 30))

# db conf
LOCAL_DB = 'http://localhost:8000'
DYNAMODB_URL = os.getenv('DYNAMODB_URL', None)

# db table conf
TABLE_AUTH = os.getenv('TABLE_AUTH', 'auth')
TABLE_ACCOUNT = os.getenv('TABLE_ACCOUNT', 'accounts')
BATCH_LIMIT = int(os.getenv('BATCH_LIMIT', '20'))

# s3 conf
FT_BUCKET = os.getenv('FT_BUCKET', 'foreign-teacher')

# email conf
EMAIL_SENDER = os.getenv('EMAIL_SENDER', None)
EMAIL_VERIFY_CODE_TEMPLATE = os.getenv('EMAIL_VERIFY_CODE_TEMPLATE', None)
EMAIL_RESET_PASSWORD_TEMPLATE = os.getenv('EMAIL_RESET_PASSWORD_TEMPLATE', None)
FRONTEND_RESET_PASSWORD_URL = os.getenv('FRONTEND_RESET_PASSWORD_URL', 'https://localhost:8002/auth/reset_password?token=')
