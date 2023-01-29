from pydantic import BaseModel

class DetailInfo(BaseModel):
    msg: str = ''
    type: str = ''
    loc: str = ''

class HTTPError(BaseModel):
    detail: DetailInfo

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