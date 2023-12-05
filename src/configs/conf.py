import os

LOCAL_REGION = os.getenv("LOCAL_REGION", "ap-northeast-1")

# cache conf
TOKEN_EXPIRE_TIME = int(os.getenv('TOKEN_EXPIRE_TIME', 60 * 60 * 24 * 30))

# db conf
LOCAL_DB = 'http://localhost:8000'
DYNAMODB_URL = os.getenv('DYNAMODB_URL', 'http://localhost:8000')

# db table conf
TABLE_AUTH = os.getenv('TABLE_AUTH', 'auth')
TABLE_ACCOUNT = os.getenv('TABLE_ACCOUNT', 'accounts')
BATCH_LIMIT = int(os.getenv('BATCH_LIMIT', '20'))

# s3 conf
FT_BUCKET = os.getenv('FT_BUCKET', 'foreign-teacher')

# FB App conf
FACEBOOK_APP_ID = os.getenv('FACEBOOK_APP_ID', '829288179205024')
FACEBOOK_APP_SECRET = os.getenv('FACEBOOK_APP_SECRET', '0de1fb7a89306e010a538ef8e9da0728')
REDIRECT_URI = os.getenv('REDIRECT_URI', 'http://localhost:8002/auth/api/v2/auth-nosql/fb/login')