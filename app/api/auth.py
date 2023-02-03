from fastapi import APIRouter, Response, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Optional

from ..db import db_get_user
from ..models.user_mod import Token, UserInDB
from ..models.uni_mod import HTTPError
from ..utils.auth import OAuth2PasswordBearerWithCookie, RefreshWithCookie
from ..utils.crypto import verify_password
from ..utils.jwt import create_access_token, create_refresh_token, decode_subject

oauth2_scheme_acc = OAuth2PasswordBearerWithCookie(tokenUrl='auth/access', scheme_name='JWT')
# oauth2_scheme_ref = OAuth2PasswordBearerWithCookie(tokenUrl='auth/refresh', token_type='refresh_token')

router = APIRouter(prefix='/auth')

# Helper function
def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    user = db_get_user(username)
    if user is None:
        return None
    if not verify_password(password, user.hashpass):
        return None
    return user

@router.post('/access', tags=['Auth'], responses={
        401: {'model': HTTPError},
        200: {'model': Token}
    })
async def get_tokens(response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    user: UserInDB = authenticate_user(form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                'msg': 'Incorrect username or password',
                'loc': '',
                'type': '401 unauthorized',
            },
            headers={'WWW-Authenticate': 'Bearer'},
        )
    access_token, exp = create_access_token(user.username)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        samesite='strict',
        secure=True,
        expires=exp.strftime("%a, %d %b %Y %H:%M:%S UTC")
    )
    refresh_token, exp = create_refresh_token(user.username)
    response.set_cookie(
        key="refresh_token",
        value=f"Bearer {refresh_token}",
        httponly=True,
        samesite='strict',
        secure=True,
        expires=exp.strftime("%a, %d %b %Y %H:%M:%S UTC")
    )
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer',
    }

@router.post('/refresh', tags=['Auth'], responses={
        401: {'model': HTTPError},
        200: {'model': Token}
    })
async def refresh_token(response: Response, ref_token: str = Depends(RefreshWithCookie)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Invalid authentication credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    print('Get ref token: ', ref_token)
    payload = decode_subject(ref_token, refresh=True) # in our case subject is username
    username: str = payload.get('sub')
    print('got username', username)
    if username is None:
        raise credentials_exception
    user = db_get_user(username)
    if user is None:
        raise credentials_exception
    access_token, _ = create_access_token(user.username)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        samesite='strict',
        secure=True,
    )
    return {
        'access_token': access_token,
        'refresh_token': ref_token,
        'token_type': 'Bearer',
    }
