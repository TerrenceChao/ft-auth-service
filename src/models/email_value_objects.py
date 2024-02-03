from pydantic import BaseModel


class EmailVO(BaseModel):
    sender_id: int  # role_id
    recipient_id: int  # role_id
    subject: str
    body: str


class EmailAuthVO(EmailVO):
    sender_role: str
    recipient_role: str
