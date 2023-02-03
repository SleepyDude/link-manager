from fastapi import APIRouter, Depends, HTTPException, status


from ..models.user_mod import (
    User, UserInDB, UserReg, TokenData, ConfirmDelete, RegResp,
)
from ..models.uni_mod import HTTPError
from ..utils.crypto import get_password_hash
from ..utils.jwt import decode_subject
from ..db import db_get_user, db_put_user, db_delete_user
from .auth import oauth2_scheme_acc as oauth2_scheme

router = APIRouter(prefix='/user')

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Invalid authentication credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    payload = decode_subject(token) # in our case subject is username
    username: str = payload.get('sub')
    if username is None:
        raise credentials_exception
    token_data = TokenData(username=username)
    user = db_get_user(token_data.username)
    if user is None:
        raise credentials_exception
    return User(**user.dict())

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

@router.get('/me', tags=['Users'], responses={
    '200': {'model': User},
})
async def get_me(cur_user: User = Depends(get_current_user)):
    return cur_user