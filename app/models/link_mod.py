from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class PutLinkRequest(BaseModel):
    title: Optional[str] = None
    url: str
    created: datetime = datetime.utcnow()
    user_id: Optional[str] = None
    link_id: Optional[str] = None
