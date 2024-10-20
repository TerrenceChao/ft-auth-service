from ..infra.resources.manager import resource_manager
from ..infra.resources.handlers import *
from ..infra.client import *
from ..infra.mq import *
from ..infra.storage.global_object_storage import GlobalObjectStorage
from ..infra.db.nosql.event_repository import EventRepository
from ..infra.db.nosql.auth_repository import AuthRepository
from ..services.auth_service import AuthService
from ..services.alert_service import IAlertService


###############################################
# session/resource/connection/connect pool
###############################################

# aioboto3.Session().resource()
storage_rsc: S3ResourceHandler = resource_manager.get('storage')
db_rsc: DynamoDBResourceHandler = resource_manager.get('dynamodb')
account_db = auth_db = ddb = db_rsc

# aioboto3.Session().client()
email_rsc: SESResourceHandler = resource_manager.get('email')
event_bus_rsc: EventBridgeResourceHandler = resource_manager.get('event_bus')
failed_pub_mq_rsc: SQSResourceHandler = resource_manager.get(
    'failed_pub_mq_rsc')
failed_sub_mq_rsc: SQSResourceHandler = resource_manager.get(
    'failed_sub_mq_rsc')

# httpx AsyncClient
http_rsc: HttpResourceHandler = resource_manager.get('http')


########################
# client/repo/adapter
########################

global_object_storage = GlobalObjectStorage(storage_rsc)
event_repo = EventRepository(db_rsc)
email_client = EmailClient(email_rsc)
request_client = RequestClientAdapter(http_rsc)
# dlq(deal letter queue) for failed pub events
failed_publish_events_dlq = SqsMqAdapter(failed_pub_mq_rsc)
# dlq(deal letter queue) for failed sub events
failed_subscribed_events_dlq = SqsMqAdapter(failed_sub_mq_rsc)
# for remote events
event_bus_adapter = EventBridgeMqAdapter(event_bus_rsc)

fb_login_repo = FBLoginRepository(request_client)
google_login_repo = GoogleLoginRepository(request_client)


##############################
# service/handler/manager
##############################

# TODO: implement & DI(connect resources)
alert_svc = IAlertService()
auth_svc = AuthService(
    auth_repo=AuthRepository(),
    obj_storage=global_object_storage,
    email=email_client,
)
