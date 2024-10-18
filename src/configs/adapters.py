from ..infra.resources.manager import resource_manager
from ..infra.resources.handlers.storage_resource import S3ResourceHandler
from ..infra.resources.handlers.db_resource import DynamoDBResourceHandler
from ..infra.resources.handlers.email_resource import SESResourceHandler
from ..infra.resources.handlers.http_resource import HttpResourceHandler

# aioboto3.Session().resource()
storage_resource: S3ResourceHandler = resource_manager.get('storage')
auth_db: DynamoDBResourceHandler = resource_manager.get('dynamodb')
account_db: DynamoDBResourceHandler = resource_manager.get('dynamodb')

# aioboto3.Session().client()
email_resource: SESResourceHandler = resource_manager.get('email')

# httpx AsyncClient
http_resource: HttpResourceHandler = resource_manager.get('http')


from ..infra.storage.global_object_storage import GlobalObjectStorage
from ..infra.client.email import Email
from ..infra.client.request_client_adapter import RequestClientAdapter
from ..infra.client.facebook import FBLoginRepository
from ..infra.client.google import GoogleLoginRepository

global_object_storage = GlobalObjectStorage(storage_resource)
email_client = Email(email_resource)
request_client = RequestClientAdapter(http_resource)
fb_login_repo = FBLoginRepository(request_client)
google_login_repo = GoogleLoginRepository(request_client)
