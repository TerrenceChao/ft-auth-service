from ..infra.resources.manager import resource_manager
from ..infra.resources.handlers import *

# aioboto3.Session().resource()
storage_rsc: S3ResourceHandler = resource_manager.get('storage')
db_rsc: DynamoDBResourceHandler = resource_manager.get('dynamodb')
account_db = auth_db = ddb = db_rsc

# aioboto3.Session().client()
email_rsc: SESResourceHandler = resource_manager.get('email')
pub_failed_dlq: SQSResourceHandler = resource_manager.get('pub_failed_dlq')
sub_failed_dlq: SQSResourceHandler = resource_manager.get('sub_failed_dlq')

# httpx AsyncClient
http_rsc: HttpResourceHandler = resource_manager.get('http')




from ..infra.db.nosql.auth_repository import AuthRepository
from ..infra.db.nosql.event_repository import EventRepository
from ..infra.storage.global_object_storage import GlobalObjectStorage
from ..infra.client import *

global_object_storage = GlobalObjectStorage(storage_rsc)
event_repo = EventRepository(db_rsc)
email_client = EmailClient(email_rsc)
request_client = RequestClientAdapter(http_rsc)

fb_login_repo = FBLoginRepository(request_client)
google_login_repo = GoogleLoginRepository(request_client)




from ..services.alert_service import IAlertService
from ..services.auth_service import AuthService

# TODO: implement & DI(connect resources)
alert_svc = IAlertService()
auth_svc = AuthService(
    auth_repo=AuthRepository(),
    obj_storage=global_object_storage,
    email=email_client,
)
