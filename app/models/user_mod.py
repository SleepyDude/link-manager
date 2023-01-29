from pydantic import BaseModel, root_validator, EmailStr, validator
from typing import Optional

class User(BaseModel):
    username: str
    email: Optional[str]

class UserInDB(User):
    hashpass: str

class UserReg(User):
    password: str
    password_confirm: str

    @root_validator
    def check_password_match(cls, values):
        pw1, pw2 = values.get('password'), values.get('password_confirm')
        if pw1 != pw2:
            raise ValueError('passwords do not match')
        return values
    
    class Config:
        schema_extra = {
            'example': {
                'username': 'JohnDoe',
                'password': 'qwerty',
                'password_confirm': 'qwerty',
            }
        }

'''
    TOKENS
'''

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class ConfirmDelete(BaseModel):
    deletion_confirm: str

    @validator('deletion_confirm')
    def confirm_deletion(cls, value):
        if value != 'delete':
            raise ValueError('You should confirm deletion by typing `delete`')
        return value
    
    class Config:
        schema_extra = {
            'example': {
                'deletion_confirm': 'delete',
            }
        }

class RegResp(BaseModel):
    success: bool
    msg: str
    user: User
