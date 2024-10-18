from fastapi import status
from pydantic import BaseModel
from typing import Dict, Any

class ClientResponse(BaseModel):
    status_code: int = status.HTTP_200_OK
    headers: Dict = None    # BaseModel 不支援 native dict, any

    # response body
    res_json: Dict = None   # BaseModel 不支援 native dict, any
    res_content: Any = None # BaseModel 不支援 native dict, any
    res_text: str = None
    res_html: str = None
