from jose import jwt, JWTError
from typing import Union, Any, Tuple
from datetime import datetime, timedelta
import os

JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
JWT_REFRESH_SECRET_KEY = os.getenv('JWT_REFRESH_SECRET_KEY')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 7 days


def create_access_token(subject: Union[str, Any], expires_mins: int = None) -> Tuple[str, datetime]:
    if expires_mins is not None:
        exp_delta = datetime.utcnow() + timedelta(minutes=expires_mins)
    else:
        exp_delta = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": exp_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, ALGORITHM)
    return encoded_jwt, exp_delta

def create_refresh_token(subject: Union[str, Any], expires_mins: int = None) -> Tuple[str, datetime]:
    if expires_mins is not None:
        expires_delta = datetime.utcnow() + timedelta(minutes=expires_mins)
    else:
        expires_delta = datetime.utcnow() + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expires_delta, "sub": str(subject)}
    print('encode name', str(subject), 'to refresh token')
    encoded_jwt = jwt.encode(to_encode, JWT_REFRESH_SECRET_KEY, ALGORITHM)
    return encoded_jwt, expires_delta

def decode_subject(token: str, refresh=False) -> dict:
    '''
    return empty dict upon JWT decode error
    '''
    key = JWT_REFRESH_SECRET_KEY if refresh else JWT_SECRET_KEY
    try:
        res = jwt.decode(token, key, algorithms=[ALGORITHM])
    except JWTError as e:
        print('JWTError:', e)
        res = {}
    return res