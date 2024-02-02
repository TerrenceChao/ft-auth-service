from pydantic import BaseModel


class EmailVO(BaseModel):
    sender_id: int
    recipient_id: int
    subject: str
    body: str
