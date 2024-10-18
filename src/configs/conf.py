import os
from dotenv import load_dotenv

# stage
TESTING = os.getenv("TESTING", "dev")
STAGE = os.getenv("STAGE", "dev")

LOCAL_REGION = os.getenv("AWS_REGION", "ap-northeast-1")
MIN_PASSWORD_LENGTH = int(os.getenv("MIN_PASSWORD_LENGTH", 6))

# probe cycle secs
PROBE_CYCLE_SECS = int(os.getenv("PROBE_CYCLE_SECS", 3))

# cache conf
TOKEN_EXPIRE_TIME = int(os.getenv('TOKEN_EXPIRE_TIME', 60 * 60 * 24 * 30))

# db conf
DDB_CONNECT_TIMEOUT=int(os.getenv("DDB_CONNECT_TIMEOUT", 120))
DDB_READ_TIMEOUT=int(os.getenv("DDB_READ_TIMEOUT", 30))
DDB_MAX_ATTEMPTS=int(os.getenv("DDB_MAX_ATTEMPTS", 5))

# db table conf
TABLE_AUTH = os.getenv('TABLE_AUTH', 'auth')
TABLE_ACCOUNT = os.getenv('TABLE_ACCOUNT', 'accounts')
TABLE_ACCOUNT_INDEX = os.getenv('TABLE_ACCOUNT_INDEX', 'account_indexs')
BATCH_LIMIT = int(os.getenv('BATCH_LIMIT', '20'))

# db log table conf
TABLE_EVENT = os.getenv('TABLE_EVENT', 'auth_event_dev')
TABLE_EVENT_LOG = os.getenv('TABLE_EVENT_LOG', 'auth_event_log_dev')
MAX_RETRY = int(os.getenv('MAX_RETRY', 3))

# s3 conf
FT_BUCKET = os.getenv('FT_BUCKET', 'foreign-teacher')
S3_REGION = os.getenv('S3_REGION', 'ap-northeast-1')
S3_CONNECT_TIMEOUT=int(os.getenv("S3_CONNECT_TIMEOUT", 10))
S3_READ_TIMEOUT=int(os.getenv("S3_READ_TIMEOUT", 10))
S3_MAX_ATTEMPTS=int(os.getenv("S3_MAX_ATTEMPTS", 3))

# connection
# http
HTTP_TIMEOUT = float(os.getenv("TIMEOUT", 10.0))
HTTP_MAX_CONNECTS = int(os.getenv("MAX_CONNECTS", 20))
HTTP_MAX_KEEPALIVE_CONNECTS = int(os.getenv("MAX_KEEPALIVE_CONNECTS", 10))
HTTP_KEEPALIVE_EXPIRY = float(os.getenv("KEEPALIVE_EXPIRY", 30.0))

# FB App conf
FACEBOOK_APP_ID = os.getenv('FACEBOOK_APP_ID', '829288179205024')
FACEBOOK_APP_SECRET = os.getenv('FACEBOOK_APP_SECRET', '0de1fb7a89306e010a538ef8e9da0728')
FACEBOOK_REDIRECT_URI = os.getenv('FACEBOOK_REDIRECT_URI', 'http://localhost:8006/api/v2/auth/fb/login')

# Google App conf
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '652252489794-hf50ke4tqvp39hf27tbpfi06evsttuh8.apps.googleusercontent.com')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', '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')
GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8006/api/v2/auth/google/login')


# email conf
EMAIL_SENDER = os.getenv('EMAIL_SENDER', 'rtyufjvbn@gmail.com')
EMAIL_VERIFY_CODE_TEMPLATE = os.getenv('EMAIL_VERIFY_CODE_TEMPLATE', None)
EMAIL_RESET_PASSWORD_TEMPLATE = os.getenv('EMAIL_RESET_PASSWORD_TEMPLATE', None)
FRONTEND_RESET_PASSWORD_URL = os.getenv('FRONTEND_RESET_PASSWORD_URL', 'https://localhost:8002/auth/reset_password?token=')
SES_CONNECT_TIMEOUT=int(os.getenv("SES_CONNECT_TIMEOUT", 10))
SES_READ_TIMEOUT=int(os.getenv("SES_READ_TIMEOUT", 10))
SES_MAX_ATTEMPTS=int(os.getenv("SES_MAX_ATTEMPTS", 3))


# event bus conf
EVENT_BUS_NAME = os.getenv('EVENT_BUS_NAME', 'default')
EVENT_SOURCE = os.getenv('EVENT_SOURCE', 'ft.test')
EVENT_DETAIL_TYPE = os.getenv('EVENT_DETAIL_TYPE', 'TestEvent')

# queue conf
QUEUE_URL = os.getenv('QUEUE_URL', 'https://sqs.ap-northeast-1.amazonaws.com/123456789012/MyQueue')
MAX_MESSAGES = int(os.getenv('MAX_MESSAGES', 10))
WAIT_SECS = int(os.getenv('WAIT_SECS', 20))
