from pydantic import BaseModel
from typing import Dict, Any, Optional

class DetailInfo(BaseModel):
    msg: str = ''
    type: str = ''
    loc: str = ''

class HTTPError(BaseModel):
    detail: DetailInfo
    status_code: int
    headers: Optional[Dict[str, Any]]

    class Config:
        schema_extra = {
            "example": {
                "detail": {
                    'msg': 'HTTPException raised.',
                    'type': 'httpexception type',
                    'loc': 'username'
                }
            },
        }