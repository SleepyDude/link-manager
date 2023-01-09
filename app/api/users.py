from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from typing import Optional
from datetime import timedelta, datetime
import os

from ..models.user_mod import (
    UserInp, UserReg, UserInDB,
    Token, TokenData,
    ConfirmDelete,
)
from ..utils import verify_password, get_password_hash
from ..db import get_db_user, put_db_user, db_delete_user

JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

router = APIRouter()



def authenticate_user(username: str, password: str):
    user = get_db_user(username)
    if user is None:
        return None
    if not verify_password(password, user.Hashpass):
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInp:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Invalid authentication credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_db_user(token_data.username)
    if user is None:
        raise credentials_exception
    return UserInp(
        username=user.Username,
    )

@router.post('/token', response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user: UserInDB = authenticate_user(form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={'sub': user.Username},
        expires_delta=access_token_expires
    )
    return {
        'access_token': access_token,
        'token_type': 'Bearer',
    }

@router.post('/register')
async def register(user_reg: UserReg):
    user = get_db_user(user_reg.username)
    if user is not None:
        raise HTTPException(status_code=409, detail="Such username is already used")
    # not found - continue registration
    hash_pass = get_password_hash(user_reg.password)
    user_in_db = UserInDB(
        Username=user_reg.username,
        Hashpass=hash_pass,
    )
    put_db_user(user_in_db)
    out_user = UserInp(**user_reg.dict())
    return {'Message': 'Registration successfull!', 'User': out_user.dict()}

@router.delete('/delete_me')
async def delete_my_account(del_conf: ConfirmDelete, cur_user: UserInp = Depends(get_current_user)):
    db_delete_user(cur_user.username)
    return {'Message': f'User `{cur_user.username}` was successfully deleted'}