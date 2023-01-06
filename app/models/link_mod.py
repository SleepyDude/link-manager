from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class PutLinkRequest(BaseModel):
    title: Optional[str] = None
    url: str
