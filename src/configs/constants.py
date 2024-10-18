from .conf import LOCAL_REGION
from enum import Enum

REGION_MAPPING = {
    'us-east-1': 'us-e1',
    'us-east-2': 'us-e2',
    'us-west-1': 'us-w1',
    'us-west-2': 'us-w2',
    'ca-central-1': 'ca-c1',
    'eu-north-1': 'eu',
    'eu-west-2': 'uk',
    'eu-west-3': 'fr',
    'eu-south-1': 'it',
    'eu-central-1': 'de',
    'ap-northeast-1': 'jp',
    'ap-northeast-2': 'kr',
    'ap-southeast-1': 'sg',
    'ap-southeast-2': 'au',
    'ap-south-1': 'in',
    'sa-east-1': 'br'
}

HERE_WE_ARE = REGION_MAPPING[LOCAL_REGION]

# TODO: 感覺改成 enum type 會好一點
VALID_ROLES = set(['company', 'teacher'])

DYNAMODB_KEYWORDS = set(['role', 'region'])

class AccountType(str, Enum):
    FT = 'ft'
    FB = 'fb'
    GOOGLE = 'google'


class PubEventStatus(Enum):
    READY = 'ready'
    PUBLISHED = 'published'
    FAILED = 'failed'


class SubEventStatus(Enum):
    SUBSCRIBED = 'subscribed'
    COMPLETED = 'completed'
    FAILED = 'failed'



# event types
USER_REGISTRATION = 'user_registration'
