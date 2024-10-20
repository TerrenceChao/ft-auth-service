import json
from typing import Any
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Attr

from .ddb_error_handler import *
from ....models.event_vos import *
from ....configs.conf import TABLE_EVENT, TABLE_EVENT_LOG
from ....configs.exceptions import *
from ....repositories.event_repository import IEventRepository
from ...resources.handlers.db_resource import DynamoDBResourceHandler

from .event_schemas import *
import logging


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class EventRepository(IEventRepository):

    def __init__(self, db: DynamoDBResourceHandler):
        self.event_db = db

    '''
    UPSERT event_entity (insert OR update)
    INSERT event_log_entity
    '''
    async def append_pub_event_log(self, event: PubEventDetailVO):
        event_dict = event.dict()
        try:
            event_entity: EventEntity = EventEntity \
                .parse_obj(event_dict) \
                .update_ts() # updated_at
            event_log_entity: EventLogEntity = EventLogEntity.parse_event_entity(event_entity)
            db = await self.event_db.access()
            client = db.meta.client
            response = await client.transact_write_items(
                TransactItems=[
                    {
                        'Put': {
                            'TableName': TABLE_EVENT,
                            'Item': event_entity.dict(),
                            'ConditionExpression': 'attribute_not_exists(updated_at) OR updated_at < :new_updated_at',  # 條件檢查
                            'ExpressionAttributeValues': {
                                ':new_updated_at': event_entity.updated_at  # 直接在條件中使用值
                            }
                        }
                    },
                    {
                        'Put': {
                            'TableName': TABLE_EVENT_LOG,
                            'Item': event_log_entity.dict(),
                        }
                    },
                ]
            )
            log.info('upsert_publish_event_log. Transaction successful: %s', json.dumps(response))
            
        except ClientError as e:
            log.error(f'upsert_publish_event_log error. [create_req_error], event:{event_dict}, err:{client_err_msg(e)}')
            raise Exception(f'create_req_error: {client_err_msg(e)}')
        
        except Exception as e:
            log.error(f'upsert_publish_event_log error. [db_create_error], event:{event_dict}, err:{str(e)}')
            raise Exception(f'db_create_error: {str(e)}')


    '''
    UPSERT event_entity (insert OR update)
    INSERT event_log_entity
    '''
    async def append_sub_event_log(self, event: SubEventDetailVO):
        event_dict = event.dict()
        try:
            event_entity: EventEntity = EventEntity \
                .parse_obj(event_dict) \
                .update_ts() # updated_at
            event_log_entity: EventLogEntity = EventLogEntity.parse_event_entity(event_entity)
            db = await self.event_db.access()
            client = db.meta.client
            response = await client.transact_write_items(
                TransactItems=[
                    {
                        'Put': {
                            'TableName': TABLE_EVENT,
                            'Item': event_entity.dict(),
                            'ConditionExpression': 'attribute_not_exists(updated_at) OR updated_at < :new_updated_at',  # 條件檢查
                            'ExpressionAttributeValues': {
                                ':new_updated_at': event_entity.updated_at  # 直接在條件中使用值
                            }
                        }
                    },
                    {
                        'Put': {
                            'TableName': TABLE_EVENT_LOG,
                            'Item': event_log_entity.dict(),
                        }
                    },
                ]
            )
            log.info('upsert_subscribe_event_log. Transaction successful: %s', json.dumps(response))
            
        except ClientError as e:
            log.error(f'upsert_subscribe_event_log error. [create_req_error], event:{event_dict}, err:{client_err_msg(e)}')
            raise Exception(f'create_req_error: {client_err_msg(e)}')
        
        except Exception as e:
            log.error(f'upsert_subscribe_event_log error. [db_create_error], event:{event_dict}, err:{str(e)}')
            raise Exception(f'db_create_error: {str(e)}')
