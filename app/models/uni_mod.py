from pydantic import BaseModel
from pydantic.generics import GenericModel
from typing import Generic, Optional, TypeVar

# Generic types

DataT = TypeVar('DataT')

class DetailInfo(GenericModel, Generic[DataT]):
    msg: str = ''
    type: DataT
    loc: str = ''

class HTTPError(GenericModel, Generic[DataT]):
    detail: DetailInfo[DataT]

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