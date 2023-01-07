from pydantic import BaseModel, root_validator
from typing import Optional

class UserInp(BaseModel):
    username: str
    email: Optional[str]

class UserReg(BaseModel):
    username: str
    password: str
    password_confirm: str
    email: Optional[str]

    @root_validator
    def check_password_match(cls, values):
        pw1, pw2 = values.get('password'), values.get('password_confirm')
        if pw1 != pw2:
            raise ValueError('passwords do not match')
        return values

class UserInDB(BaseModel):
    Username: str
    Hashpass: str
    Email: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
