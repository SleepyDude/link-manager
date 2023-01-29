from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from typing import Optional, Literal
from datetime import timedelta, datetime
import os

from ..models.user_mod import (
    User, UserInDB, UserReg,
    Token, TokenData,
    ConfirmDelete,
    RegResp,
)
from ..models.uni_mod import (
    HTTPError
)
from ..utils import verify_password, get_password_hash
from ..db import (
    db_get_user, db_put_user, db_delete_user
)

JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

router = APIRouter()

def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    user = db_get_user(username)
    if user is None:
        return None
    if not verify_password(password, user.hashpass):
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

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
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
    user = db_get_user(token_data.username)
    if user is None:
        raise credentials_exception
    return User(**user.dict())

@router.post('/token', response_model=Token, tags=['Users'])
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
        data={'sub': user.username},
        expires_delta=access_token_expires
    )
    return {
        'access_token': access_token,
        'token_type': 'Bearer',
    }

@router.post('/register', tags=['Users'], responses={
        409: {'model': HTTPError},
        200: {'model': RegResp}
    })
async def register(user_reg: UserReg):
    user = db_get_user(user_reg.username)
    if user is not None:
        raise HTTPException(status_code=409, detail={
            'msg': 'Such username is already used',
            'loc': 'username',
            'type': '409 Conflict',
        })
    # not found - continue registration
    hash_pass = get_password_hash(user_reg.password)
    user_in_db = UserInDB(
        username=user_reg.username,
        hashpass=hash_pass,
    )
    db_put_user(user_in_db)
    out_user = User(**user_reg.dict())
    return RegResp(
        success=True,
        msg='Registration successfull.',
        user=out_user
    )

@router.delete('/delete_me', tags=['Users'])
async def delete_my_account(_: ConfirmDelete, cur_user: User = Depends(get_current_user)):
    db_delete_user(cur_user.username)
    return {'Message': f'User `{cur_user.username}` was successfully deleted'}