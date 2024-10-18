from fastapi import status
from typing import Dict
from ..app_templates.request_client import IRequestClient
from ..app_templates.models.client_response import ClientResponse
from ..resources.handlers.http_resource import HttpResourceHandler
from ...configs.exceptions import *
import logging


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


SUCCESS_CODE = "0"


class RequestClientAdapter(IRequestClient):
    def __init__(self, connect: HttpResourceHandler):
        self.connect = connect


    """
    return response body only
    """
    async def simple_get(self, url: str, params: Dict = None, headers: Dict = None) -> (Dict[str, str] | None):
        result = None
        response = None
        try:
            client = await self.connect.access(url=url) # self.connect.access(**kwargs) 
            response = await client.get(url, params=params, headers=headers)
            result = response.json()

        except Exception as e:
            log.error(f"simple_get request error, url:%s, params:%s, headers:%s, resp:%s, err:%s",
                    url, params, headers, response, e.__str__())
            raise ServerException(msg='get_connection_error')
            
        self.__status_code_validation(
            response=response,
            method='GET',
            url=url,
            body=None,
            params=params,
            headers=headers,
        )

        return result


    async def get(self, url: str, params: Dict = None, headers: Dict = None) -> ClientResponse:
        # TODO: implement the method
        return ClientResponse()

    """
    return response body only
    """
    async def simple_post(self, url: str, json: Dict, headers: Dict = None) -> (Dict[str, str] | None):
        result = None
        response = None
        try:
            client = await self.connect.access(url=url) # self.connect.access(**kwargs)
            response = await client.post(url, json=json, headers=headers)
            result = response.json()

        except Exception as e:
            log.error(f"simple_post request error, url:%s, json:%s, headers:%s, resp:%s, err:%s",
                    url, json, headers, response, e.__str__())
            raise ServerException(msg='post_connection_error')
            
        self.__status_code_validation(
            response=response,
            method='POST',
            url=url,
            body=json,
            params=None,
            headers=headers,
        )

        return result


    async def post(self, url: str, json: Dict, headers: Dict = None) -> ClientResponse:
        # TODO: implement the method
        return ClientResponse()

    """
    return response body only
    """
    async def simple_put(self, url: str, json: Dict = None, headers: Dict = None) -> (Dict[str, str] | None):
        result = None
        response = None
        try:
            client = await self.connect.access(url=url) # self.connect.access(**kwargs)
            response = await client.put(url, json=json, headers=headers)
            result = response.json()

        except Exception as e:
            log.error(f"simple_put request error, url:%s, json:%s, headers:%s, resp:%s, err:%s",
                    url, json, headers, response, e.__str__())
            raise ServerException(msg='put_connection_error')
            
        self.__status_code_validation(
            response=response,
            method='PUT',
            url=url,
            body=json,
            params=None,
            headers=headers,
        )

        return result


    async def put(self, url: str, json: Dict = None, headers: Dict = None) -> ClientResponse:
        # TODO: implement the method
        return ClientResponse()

    """
    return response body only
    """
    async def simple_delete(self, url: str, params: Dict = None, headers: Dict = None) -> (Dict[str, str] | None):
        result = None
        response = None
        try:
            client = await self.connect.access(url=url) # self.connect.access(**kwargs)
            response = await client.delete(url, params=params, headers=headers)
            result = response.json()

        except Exception as e:
            log.error(f"simple_delete request error, url:%s, params:%s, headers:%s, resp:%s, err:%s",
                    url, params, headers, response, e.__str__())
            raise ServerException(msg='delete_connection_error')
            
        self.__status_code_validation(
            response=response,
            method='DEL',
            url=url,
            body=None,
            params=params,
            headers=headers,
        )

        return result


    async def delete(self, url: str, params: Dict = None, headers: Dict = None) -> ClientResponse:
        # TODO: implement the method
        return ClientResponse()
   
    def __status_code_validation(self, response: HttpResourceHandler.Response, method: str, url: str, body: Dict = None, params: Dict = None, headers: Dict = None):
        status_code = response.status_code
        if status_code < 400:
            return
        

        # 处理错误响应
        response_json = response.json()  # 尝试解析 JSON 响应
        msg = response_json.get("msg", "unknow_error")  # 获取错误消息
        data = response_json.get("data", None)  # 获取数据

        log.error(f"service request fail, [%s]: %s, body:%s, params:%s, headers:%s, status_code:%s, msg:%s, \n response:%s", 
                method, url, body, params, headers, status_code, msg, response)

        if status_code == status.HTTP_400_BAD_REQUEST:
            raise ClientException(msg=msg, data=data)
        
        if status_code == status.HTTP_401_UNAUTHORIZED:
            raise UnauthorizedException(msg=msg, data=data)
        
        if status_code == status.HTTP_403_FORBIDDEN:
            raise ForbiddenException(msg=msg, data=data)
        
        if status_code == status.HTTP_404_NOT_FOUND:
            raise NotFoundException(msg=msg, data=data)
        
        if status_code == status.HTTP_406_NOT_ACCEPTABLE:
            raise NotAcceptableException(msg=msg, data=data)
        
        raise ServerException(msg=msg, data=data)
            

    def __err(self, resp_json):
        return not "code" in resp_json or resp_json["code"] != SUCCESS_CODE

    def __err_resp(self, resp_json):
        if "detail" in resp_json:
            return str(resp_json["detail"])
        if "msg" in resp_json:
            return str(resp_json["msg"])
        if "message" in resp_json:
            return str(resp_json["message"])

        log.error(f"cannot find err msg, resp_json:{resp_json}")
        return "service reqeust error"
