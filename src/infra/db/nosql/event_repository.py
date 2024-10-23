import json
from typing import Any, Tuple
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Attr

from .ddb_error_handler import *
from ....models.event_vos import *
from ....configs.conf import TABLE_EVENT, TABLE_EVENT_LOG, TABLE_ACCOUNT_INDEX
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
                .create_ts() # created_at
            event_log_entity: EventLogEntity = EventLogEntity.parse_event_entity(event_entity)
            db = await self.event_db.access()
            client = db.meta.client

            (last_created, last_updated) = \
                await self.get_last_event_times(client, event_entity.event_id)
            if event_entity.updated_at <= last_updated:
                log.info('upsert_publish_event_log. updated_at is not newer than the existing one.\
                            last_updated: %s, new: %s', last_updated, event_entity.updated_at)
                return
            
            if last_created > 0:
                event_entity.created_at = last_created

            response = await client.transact_write_items(
                TransactItems=[
                    {
                        'Put': {
                            'TableName': TABLE_EVENT,
                            'Item': event_entity.dict(),
                        }
                    },
                    {
                        'Put': {
                            'TableName': TABLE_EVENT_LOG,
                            'Item': event_log_entity.dict(),
                        }
                    },
                    {
                        'Update': {
                            'TableName': TABLE_ACCOUNT_INDEX,
                            'Key': {
                                'role_id': event.role_id, # partition key
                            },
                            'UpdateExpression': 'SET #event_id = :event_id, #updated_at = :updated_at ',
                            'ExpressionAttributeNames': {
                                '#event_id': 'event_id',
                                '#updated_at': 'updated_at', 
                            },
                            'ExpressionAttributeValues': {
                                ':event_id': event_entity.event_id,
                                ':updated_at': event_entity.updated_at,
                            },
                            'ReturnValuesOnConditionCheckFailure': 'ALL_OLD'  # 如果条件检查失败时返回旧的值
                        },
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
                .create_ts() # created_at
            event_log_entity: EventLogEntity = EventLogEntity.parse_event_entity(event_entity)
            db = await self.event_db.access()
            client = db.meta.client

            (last_created, last_updated) = \
                await self.get_last_event_times(client, event_entity.event_id)
            if event_entity.updated_at <= last_updated:
                log.info('upsert_subscribe_event_log. updated_at is not newer than the existing one.\
                            last_updated: %s, new: %s', last_updated, event_entity.updated_at)
                return
            
            if last_created > 0:
                event_entity.created_at = last_created

            response = await client.transact_write_items(
                TransactItems=[
                    {
                        'Put': {
                            'TableName': TABLE_EVENT,
                            'Item': event_entity.dict(),
                        }
                    },
                    {
                        'Put': {
                            'TableName': TABLE_EVENT_LOG,
                            'Item': event_log_entity.dict(),
                        }
                    },
                    {
                        'Update': {
                            'TableName': TABLE_ACCOUNT_INDEX,
                            'Key': {
                                'role_id': event.role_id, # partition key
                            },
                            'UpdateExpression': 'SET #event_id = :event_id, #updated_at = :updated_at ',
                            'ExpressionAttributeNames': {
                                '#event_id': 'event_id',
                                '#updated_at': 'updated_at', 
                            },
                            'ExpressionAttributeValues': {
                                ':event_id': event_entity.event_id,
                                ':updated_at': event_entity.updated_at,
                            },
                            'ReturnValuesOnConditionCheckFailure': 'ALL_OLD'  # 如果条件检查失败时返回旧的值
                        },
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


    async def get_last_event_times(self, client: Any, event_id: int) -> Tuple[int, int]:
        response = await client.get_item(
            TableName=TABLE_EVENT,
            Key={'event_id': event_id},
            ProjectionExpression='created_at, updated_at',
        )
        if 'Item' in response:
            item = dict(response['Item'])
            created_at = item.get('created_at', 0)
            updated_at = item.get('updated_at', 0)
            return (
                created_at if created_at else 0,
                updated_at if updated_at else 0,
            )
        else:
            return (0, 0)
