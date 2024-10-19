import json
from typing import Any
from botocore.exceptions import ClientError

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

    async def append_pub_event_log(self, event: PubEventDetailVO):
        event_dict = event.dict()
        try:
            event_entity: EventEntity = EventEntity \
                .parse_obj(event_dict) \
                .create_ts() # create_at
            event_log_entity: EventLogEntity = EventLogEntity.parse_event_entity(event_entity)
            db = await self.event_db.access()
            client = db.meta.client
            response = await client.transact_write_items(
                TransactItems=[
                    {
                        # TODO: 做到 upsert
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
                ]
            )
            log.info('create_pub_event. Transaction successful: %s', json.dumps(response))
            
        except ClientError as e:
            log.error(f'create_pub_event error. [create_req_error], event:{event_dict}, err:{client_err_msg(e)}')
            raise Exception(f'create_req_error: {client_err_msg(e)}')
        
        except Exception as e:
            log.error(f'create_pub_event error. [db_create_error], event:{event_dict}, err:{str(e)}')
            raise Exception(f'db_create_error: {str(e)}')


    async def update_pub_event_log_status(self, event: PubEventDetailVO):
        event_dict = event.dict()
        try:
            event_entity: EventEntity = EventEntity \
                .parse_obj(event.dict()) \
                .update_ts() # update_at
            event_log_entity: EventLogEntity = EventLogEntity.parse_event_entity(event_entity)
            db = await self.event_db.access()
            client = db.meta.client
            response = await client.transact_write_items(
                TransactItems=[
                    {
                        'Update': {
                            'TableName': TABLE_EVENT,
                            'Key': {'PrimaryKey': {'N': str(event.event_id)}},
                            'UpdateExpression': 'SET #status = :status, #updated_at = :updated_at',
                            'ExpressionAttributeNames': {
                                '#status': 'status',
                                '#updated_at': 'updated_at'
                            },
                            'ExpressionAttributeValues': {
                                ':status': {'S': event.status},
                                ':updated_at': {'N': str(gen_timestamp())}
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
            log.info('update_pub_event_log_status. Transaction successful: %s', json.dumps(response))
            
        except ClientError as e:
            log.error(f'update_pub_event_log_status error.[update_req_error], event:{event_dict}, err:{client_err_msg(e)}')
            raise Exception(f'update_req_error: {client_err_msg(e)}')
        
        except Exception as e:
            log.error(f'update_pub_event_log_status error. [db_update_error], event:{event_dict}, err:{str(e)}')
            raise Exception(f'db_update_error: {str(e)}')
        

    async def append_sub_event_log(self, event: SubEventDetailVO):
        event_dict = event.dict()
        try:
            event_entity: EventEntity = EventEntity \
                .parse_obj(event_dict) \
                .create_ts() # create_at
            event_log_entity: EventLogEntity = EventLogEntity.parse_event_entity(event_entity)
            db = await self.event_db.access()
            client = db.meta.client
            response = await client.transact_write_items(
                TransactItems=[
                    {
                        # TODO: 做到 upsert
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
                ]
            )
            log.info('create_sub_event. Transaction successful: %s', json.dumps(response))
            
        except ClientError as e:
            log.error(f'create_sub_event error. [create_req_error], event:{event_dict}, err:{client_err_msg(e)}')
            raise Exception(f'create_req_error: {client_err_msg(e)}')
        
        except Exception as e:
            log.error(f'create_sub_event error. [db_create_error], event:{event_dict}, err:{str(e)}')
            raise Exception(f'db_create_error: {str(e)}')

    async def update_sub_event_log_status(self, event: SubEventDetailVO):
        event_dict = event.dict()
        try:
            event_entity: EventEntity = EventEntity \
                .parse_obj(event.dict()) \
                .update_ts() # update_at
            event_log_entity: EventLogEntity = EventLogEntity.parse_event_entity(event_entity)
            db = await self.event_db.access()
            client = db.meta.client
            response = await client.transact_write_items(
                TransactItems=[
                    {
                        'Update': {
                            'TableName': TABLE_EVENT,
                            'Key': {'PrimaryKey': {'N': str(event.event_id)}},
                            'UpdateExpression': 'SET #status = :status, #updated_at = :updated_at',
                            'ExpressionAttributeNames': {
                                '#status': 'status',
                                '#updated_at': 'updated_at'
                            },
                            'ExpressionAttributeValues': {
                                ':status': {'S': event.status},
                                ':updated_at': {'N': str(gen_timestamp())}
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
            log.info('update_sub_event_log_status. Transaction successful: %s', json.dumps(response))
            
        except ClientError as e:
            log.error(f'update_sub_event_log_status error.[update_req_error], event:{event_dict}, err:{client_err_msg(e)}')
            raise Exception(f'update_req_error: {client_err_msg(e)}')
        
        except Exception as e:
            log.error(f'update_sub_event_log_status error. [db_update_error], event:{event_dict}, err:{str(e)}')
            raise Exception(f'db_update_error: {str(e)}')
