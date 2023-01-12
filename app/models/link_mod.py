from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class Link(BaseModel):
    created: Optional[datetime] = None
    priority_num: str
    title: Optional[str] = None
    url: str
    icon: Optional[str] = None
    tags: List[str] = []

class LinkInDB(Link):
    PK: str
    SK: str

class LinkInp(BaseModel):
    title: Optional[str] = None
    url: str

class LinkListParams(BaseModel):
    offset: Optional[str] = ""
    limit: Optional[int] = None

class PutLinkRequest(BaseModel):
    title: Optional[str] = None
    url: str

class LinkList(BaseModel):
    Listname: str
    LastAdd: Optional[datetime]
    Elements: int = 0