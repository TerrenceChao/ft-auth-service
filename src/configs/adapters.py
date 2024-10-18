from ..infra.resources.manager import resource_manager
from ..infra.resources.handlers.storage_resource import S3ResourceHandler
from ..infra.resources.handlers.db_resource import DynamoDBResourceHandler
from ..infra.resources.handlers.email_resource import SESClientHandler
from ..infra.resources.handlers.http_resource import HttpResourceHandler

# aioboto3.Session().resource()
storage_resource: S3ResourceHandler = resource_manager.get('storage')
auth_db: DynamoDBResourceHandler = resource_manager.get('dynamodb')
account_db: DynamoDBResourceHandler = resource_manager.get('dynamodb')

# aioboto3.Session().client()
email_client: SESClientHandler = resource_manager.get('email')

# httpx AsyncClient
http_resource: HttpResourceHandler = resource_manager.get('http')
