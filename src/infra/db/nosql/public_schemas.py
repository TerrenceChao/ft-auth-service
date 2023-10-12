from typing import Optional
from pydantic import BaseModel
from ...utils.time_util import gen_timestamp


class BaseEntity(BaseModel):
    created_at: Optional[int] = None
    updated_at: Optional[int] = None

    def create_ts(self):
        ts = gen_timestamp()
        self.created_at = ts
        self.updated_at = ts
        return self

    def update_ts(self):
        self.updated_at = gen_timestamp()
        return self
